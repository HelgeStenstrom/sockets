import time
import unittest

import Robotics


class Ncd_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = Robotics.MaturoNCD()

    def tearDown(self):
        pass

    def test_that_some_simple_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("*IDN? "), Robotics.MaturoNCD.Idn_response)
        self.assertEqual(self.rd.commandFor("CP  "), Robotics.MaturoNCD.CP_response)
        self.assertEqual(self.rd.commandFor("BU  ; "), Robotics.MaturoNCD.BU_Response)

    def test_that_parametrized_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("LD -123.4 DG NP GO"),
                         Robotics.MaturoNCD.LD_NP_GO_response, "negative fraction")
        self.assertEqual(self.rd.commandFor("LD 12.3 DG NP GO"),
                         Robotics.MaturoNCD.LD_NP_GO_response, "postitive fraction")
        self.assertEqual(self.rd.commandFor("LD 12 DG NP GO"),
                         Robotics.MaturoNCD.LD_NP_GO_response, "integer argument")
        self.assertEqual(self.rd.commandFor("LD 7 SP"),
                         Robotics.MaturoNCD.LD_SP_response, "speed on 1-8 scale")
        self.assertEqual(self.rd.commandFor("SP"),
                         Robotics.MaturoNCD.SP_response, "Returned speed")
        self.assertEqual(self.rd.commandFor("LD 1 DV"),
                         Robotics.MaturoNCD.LD_dev_DV_response, "Select current device")


class Ncd_response_FrontDoor_Tests(unittest.TestCase):
    def setUp(self):
        self.ncd = Robotics.MaturoNCD()
        self.ncd.responseFunction("LD 1 DV")

    def tearDown(self):
        pass

    def test_that_unknown_command_returns_error_message(self):
        cmd = 'bad command'
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response[0:3], "E -")

    def test_that_idn_returns_identity(self):
        cmd = '*IDN?'
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "Maturo,NCD_266")

    def test_that_opt_is_not_a_command(self):
        cmd = "*OPT?"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "E - x")

    def test_that_movement_cmd_is_silent(self):
        # The behavior of Maturo NCD is different from innco CO3000.
        cmd = "LD -123.4 DG NP GO"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")

    def test_that_device_selection_is_silent(self):
        # The behavior of Maturo NCD is different from innco CO3000.
        cmd = "LD 1 DV"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")

    @staticmethod
    def positionSetup(dev):
        # TODO: Flytta funktionen, använd den för RotaryDisc också.
        dev.movementStartTime = time.time()
        dev.targetPosition = -12.34
        dev.startPosition = -12.34
        dev.currentPosition = -12.34
        dev.speedInDegPerSecond = 3

    def test_that_CP_returns_current_position_integer(self):
        cd = self.ncd.currentDevice
        self.positionSetup(cd)
        cmd = "CP"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "-12")

    def test_that_RP_returns_current_position_integer(self):
        cd = self.ncd.currentDevice
        self.positionSetup(cd)
        cmd = "RP"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "-12.34")

    def test_that_ST_is_silent(self):
        cmd = "ST"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")


class Ncd_response_BackDoor_Tests(unittest.TestCase):
    def setUp(self):
        self.ncd = Robotics.MaturoNCD()
        rotDevices = [dev for dev in self.ncd.attachedDevices if isinstance(dev, Robotics.OneRotaryDisc)]
        self.ncd.currentDevice = rotDevices[0]

    def tearDown(self):
        pass

    def test_that_starting_movement_causes_busy(self):
        cmd = "LD -123.4 DG NP GO"
        self.assertEqual(self.ncd.isBusy(), False)
        self.ncd.responseFunction(cmd)
        self.assertEqual(self.ncd.isBusy(), True)

    def test_BU_response_before_and_after_setting_new_position(self):
        # Normally, these are set when the movement is started.
        # TODO: Dela upp i två tester: OneRotaryDisc busy-flagga, samt att de påverkar isBusy() i denna klass
        # TODO: Gör en test helper function, och ta bort test code duplication. NCD vs RotaryDisc
        cd = self.ncd.currentDevice
        cd.startPosition = 0
        cd.movementStartTime = time.time()
        cd.targetPosition = 0

        before = self.ncd.responseFunction("BU")
        self.assertEqual(before, "0")
        self.ncd.responseFunction("LD 123.4 DG NP GO")
        after = self.ncd.responseFunction("BU")
        self.assertEqual(after, "1")
        cd.finalizeMovement()
        after2 = self.ncd.responseFunction("BU")
        self.assertEqual(after2, "0")

    def test_that_movement_goal_is_set(self):
        # TODO: kanske vi inte ska testa på detta sätt. Viktigare att startMovement anropas.
        # Försök med Mock, MagicMock
        cmd = "LD -123.4 DG NP GO"
        self.ncd.responseFunction(cmd)
        self.assertEqual(self.ncd.currentDevice.targetPosition, -123.4)

    def test_that_the_speed_can_be_set(self):
        # TODO: Förstå och förenkla detta test, och namnen i RotaryDisc
        n1, n2 = self.ncd.devNamesToAttach[0:2]
        dev1 = self.ncd.deviceByName(n1)
        dev2 = self.ncd.deviceByName(n2)

        def cmdString(name):
            return "LD %s DV" % name

        self.ncd.responseFunction(cmdString(n1))
        cd = self.ncd.currentDevice
        self.assertEqual(cd.speedInDegPerSecond, 4.9)
        cmd = "LD 5 SP"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")
        self.assertEqual(cd.speedInDegPerSecond, 5)
        self.ncd.responseFunction(cmdString(n2))
        self.ncd.responseFunction("LD 4 SP")
        self.assertEqual(dev1.speedInDegPerSecond, 5)
        self.assertEqual(dev2.speedInDegPerSecond, 4)

    def test_that_speed_is_returned(self):
        self.ncd.currentDevice.speedInDegPerSecond = 7
        cmd = "SP"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "7")

    def test_that_movement_takes_limited_time_and_reaches_target(self):
        cd = self.ncd.currentDevice
        cd.currentPosition = 0
        timeItShouldTake = 0.02
        cd.speedInDegPerSecond = 100 / timeItShouldTake

        self.ncd.responseFunction("LD 100 DG NP GO")
        response = self.ncd.responseFunction("BU")
        self.assertEqual(response, "1")
        time.sleep(timeItShouldTake * 1.3)  # Need to agree with slowDown in update function.
        response = self.ncd.responseFunction("BU")
        self.assertNotEqual(cd.currentPosition, 0)
        self.assertEqual(response, "0")
        self.assertEqual(cd.currentPosition, 100)

    def test_that_movement_takes_time(self):
        cd = self.ncd.currentDevice
        cd.currentPosition = 0
        timeItShouldTake = 0.08
        cd.speedInDegPerSecond = 100 / timeItShouldTake

        self.ncd.responseFunction("LD 100 DG NP GO")
        time.sleep(timeItShouldTake * 0.5)  # Half the distance in half the time.
        response = self.ncd.responseFunction("CP")
        self.assertNotEqual(response, "0")
        self.assertGreater(cd.currentPosition, 0)
        self.assertLess(cd.currentPosition, 95)

    def test_that_ST_stops_the_movement(self):
        current = self.ncd.currentDevice
        current.busy = True
        cmd = "ST"
        self.ncd.responseFunction(cmd)
        self.assertEqual(current.busy, False)

    def test_that_limits_can_be_set_and_read_back(self):
        # exercise SUT, pre-conditions
        cmd = "LD 123 DG WL"
        response = self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")
        cmd = "LD -93.2 DG CL"
        self.ncd.responseFunction(cmd)
        self.assertEqual(response, "")

        # check result
        rightLimit = self.ncd.responseFunction("WL")
        leftLimit = self.ncd.responseFunction("CL")
        self.assertEqual(rightLimit, "123.00")
        self.assertEqual(leftLimit, "-93.20")


class Ncd_AntennaStand_response_tests(unittest.TestCase):
    def setUp(self):
        self.ncd = Robotics.MaturoNCD()
        self.ncd.currentDevice = self.ncd.deviceByName("0")
        self.assertIsInstance(self.ncd.currentDevice, Robotics.AntennaStand)

    def test_polarization_commands(self):
        self.ncd.responseFunction("PV")
        vResponse = self.ncd.responseFunction("P?")
        self.assertEqual(vResponse, "1")

        self.ncd.responseFunction("PH")
        hResponse = self.ncd.responseFunction("P?")
        self.assertEqual(hResponse, "0")

    def test_sp_command_on_antenna_stand(self):
        antennaStand = self.ncd.deviceByName("0")
        # Precondition
        self.assertIsInstance(antennaStand, Robotics.AntennaStand, "we need an AntennaStand for the test")

        self.ncd.currentDevice = antennaStand
        response = self.ncd.responseFunction("SP?")
        self.assertEqual(response, "E - V")

    def test_pol_command_on_rotary_disc(self):
        ttDevice = self.ncd.deviceByName("1")
        # Precondition
        self.assertIsInstance(ttDevice, Robotics.OneRotaryDisc, "we need a OneRotaryDisc for the test")

        self.ncd.currentDevice = ttDevice
        response = self.ncd.responseFunction("P?")
        self.assertEqual(response, "E - V")
        response = self.ncd.responseFunction("PH")
        self.assertEqual(response, "E - V")
        response = self.ncd.responseFunction("PV")
        self.assertEqual(response, "E - V")


class Ncd_top_level_function_tests(unittest.TestCase):
    def setUp(self):
        self.rd = Robotics.MaturoNCD()

    def tearDown(self):
        pass

    def test_that_a_device_can_be_found_by_name(self):
        devs = self.rd.attachedDevices
        devsByName = [self.rd.deviceByName(n) for n in self.rd.devNamesToAttach]
        self.assertEqual(set(devs), set(devsByName))
