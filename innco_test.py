import time
import unittest

import Robotics
import socketInstrument


class rotary_Tests(unittest.TestCase):
    # TODO: testa att offset och random fungerar som kommandots argument.
    def setUp(self):
        self.rd = Robotics.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_devices_have_names(self):
        devs = self.rd.attachedDevices
        names = [dev.name for dev in devs]
        self.assertListEqual(names, self.rd.devNamesToAttach)

    def test_that_some_simple_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("*IDN? "), Robotics.RotaryDiscBySocket.Idn_response)
        self.assertEqual(self.rd.commandFor("*OPT? "), Robotics.RotaryDiscBySocket.OPT_response)
        self.assertEqual(self.rd.commandFor("CP  "), Robotics.RotaryDiscBySocket.CP_response)
        self.assertEqual(self.rd.commandFor("BU  ; "), Robotics.RotaryDiscBySocket.BU_Response)

    def test_that_parametrized_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("LD -123.4 DG NP GO"),
                         Robotics.RotaryDiscBySocket.LD_NP_GO_response, "negative fraction")
        self.assertEqual(self.rd.commandFor("LD 12.3 DG NP GO"),
                         Robotics.RotaryDiscBySocket.LD_NP_GO_response, "postitive fraction")
        self.assertEqual(self.rd.commandFor("LD 12 DG NP GO"),
                         Robotics.RotaryDiscBySocket.LD_NP_GO_response, "integer argument")
        self.assertEqual(self.rd.commandFor("LD 12.3 NSP"),
                         Robotics.RotaryDiscBySocket.LD_NSP_response, "speed in deg per second")
        self.assertEqual(self.rd.commandFor("NSP"),
                         Robotics.RotaryDiscBySocket.NSP_response, "Returned speed")
        self.assertEqual(self.rd.commandFor("LD DS2 DV"),
                         Robotics.RotaryDiscBySocket.LD_dev_DV_response, "Select current device")

    def test_distance_function(self):
        limit = self.rd.farDistance
        self.assertTrue(self.rd.isDistant(limit+1))
        self.assertFalse(self.rd.isDistant(limit-1))


class rotary_response_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = Robotics.RotaryDiscBySocket()
        # TODO: välj ett device som "current"

    def tearDown(self):
        pass

    def test_that_unknown_command_returns_error_message(self):
        cmd = 'bad command'
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response[0:3], "E -")

    def test_that_idn_returns_identity(self):
        cmd = '*IDN?'
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "innco GmbH,CO3000,python,1.02.62")

    def test_that_opt_returns_options(self):
        cmd = '*OPT?'
        response = self.rd.responseFunction(cmd)
        expected = ','.join(self.rd.devNamesToAttach)
        self.assertEqual(response, expected)

    def test_that_starting_movement_causes_busy(self):
        cmd = "LD -123.4 DG NP GO"
        self.assertEqual(self.rd.isBusy(), False)
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.isBusy(), True)

    def test_BU_response_before_and_after_setting_new_position(self):
        # Normally, these are set when the movement is started.
        # TODO: Dela upp i två tester: OneRotaryDisc busy-flagga, samt att de påverkar isBusy() i denna klass
        cd = self.rd.currentDevice
        cd.startPosition = 0
        cd.movementStartTime = time.time()
        cd.targetPosition = 0

        before = self.rd.responseFunction("BU")
        self.assertEqual(before, "0")
        self.rd.responseFunction("LD 123.4 DG NP GO")
        after = self.rd.responseFunction("BU")
        self.assertEqual(after, "1")
        cd.finalizeMovement()
        after2 = self.rd.responseFunction("BU")
        self.assertEqual(after2, "0")

    # @unittest.skip("Behövs senare, där device-klassen används.")
    def test_that_one_busy_dev_makes_whole_unit_busy(self):
        devices = self.rd.attachedDevices
        self.assertGreater(len(devices), 1)
        for dev in devices:
            dev.busy = False
        self.assertFalse(self.rd.isBusy())
        devices[0].busy = True
        self.assertTrue(self.rd.isBusy())

    def test_that_movement_goal_is_set(self):
        # TODO: kanske vi inte ska testa på detta sätt. Viktigare att startMovement anropas.
        # Försök med Mock, MagicMock
        cmd = "LD -123.4 DG NP GO"
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.currentDevice.targetPosition, -123.4)

    # @unittest.skip("")
    def test_that_movement_goal_is_returned(self):
        cmd = "LD -123.4 DG NP GO"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "-123.4")

    def test_that_active_device_current_postition_is_returned(self):
        cd = self.rd.currentDevice
        cd.movementStartTime = time.time()
        thePos = -123.4
        cd.targetPosition = thePos
        cd.startPosition = thePos
        cd.currentPosition = thePos
        cd.speedInDegPerSecond = 3
        cmd = "CP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "-123.4")


    def test_that_the_speed_can_be_set(self):
        # TODO: Förstå och förenkla detta test, och namnen i NCD
        n1, n2 = self.rd.devNamesToAttach[0:2]
        dev1 = self.rd.deviceByName(n1)
        dev2 = self.rd.deviceByName(n2)

        def cmdString(name):
            return "LD %s DV" % name
        self.rd.responseFunction(cmdString(n1))
        cd = self.rd.currentDevice
        cmd = "LD 5.2 NSP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "5.2")
        self.assertEqual(cd.speedInDegPerSecond, 5.2)
        self.rd.responseFunction(cmdString(n2))
        self.rd.responseFunction("LD 3.1 NSP")
        self.assertEqual(dev1.speedInDegPerSecond, 5.2)
        self.assertEqual(dev2.speedInDegPerSecond, 3.1)

    def test_that_speed_is_returned(self):
        self.rd.currentDevice.speedInDegPerSecond = 3.2
        cmd = "NSP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "3.2")

    def test_that_movement_takes_limited_time_and_reaches_target(self):
        cd = self.rd.currentDevice
        cd.currentPosition = 0
        timeItShouldTake = 0.02
        cd.speedInDegPerSecond = 100/timeItShouldTake

        self.rd.responseFunction("LD 100 DG NP GO")
        response = self.rd.responseFunction("BU")
        self.assertEqual(response, "1")
        time.sleep(timeItShouldTake*1.3)  # Need to agree with slowDown in update function.
        response = self.rd.responseFunction("BU")
        self.assertNotEqual(cd.currentPosition, 0)
        self.assertEqual(response, "0")
        self.assertEqual(cd.currentPosition, 100)

    def test_that_movement_takes_time(self):
        cd = self.rd.currentDevice
        cd.currentPosition = 0
        timeItShouldTake = 0.08
        cd.speedInDegPerSecond = 100/timeItShouldTake

        self.rd.responseFunction("LD 100 DG NP GO")
        time.sleep(timeItShouldTake * 0.5)  # Half the distance in half the time.
        response = self.rd.responseFunction("CP")
        self.assertNotEqual(response, "0")
        self.assertGreater(cd.currentPosition, 0)
        self.assertLess(cd.currentPosition, 95)


class Rotary_top_level_function_tests(unittest.TestCase):
    def setUp(self):
        self.rd = Robotics.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_a_device_can_be_found_by_name(self):
        devs = self.rd.attachedDevices
        devsByName = [self.rd.deviceByName(n) for n in self.rd.devNamesToAttach]
        self.assertEqual(devs, devsByName)


class Rotary_command_tests(unittest.TestCase):
    def setUp(self):
        self.rd = Robotics.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_LD_DV_command_is_parsed(self):
        pass

    def test_that_a_device_is_selected(self):
        cmd = "LD DS2 DV"
        self.rd.responseFunction(cmd)
        # TODO: Kolla att DS1 blir current device
        self.assertEqual(self.rd.currentDevice, self.rd.deviceByName('DS2'))


class rotary_Functions_tests(unittest.TestCase):

    def setUp(self):
        self.rd = Robotics.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_movement_completion_works(self):
        self.rd.currentDevice.currentPosition = 0
        self.rd.currentDevice.targetPosition = 123.4

        self.rd.currentDevice.finalizeMovement()

        self.assertFalse(self.rd.isBusy())
        self.assertAlmostEqual(self.rd.currentDevice.targetPosition, self.rd.currentDevice.currentPosition,
                               "not close enough", 0.1)


class OneRotaryDisc_tests(unittest.TestCase):
    def setUp(self):
        self.dev = Robotics.OneRotaryDisc('someName')

    def tearDown(self):
        pass

    def test_create_one_device(self):
        self.assertEqual(self.dev.name, 'someName')

    def test_that_it_has_limits(self):
        self.assertGreater(self.dev.limit_clockwise, self.dev.limit_anticlockwise)

    def test_busy_before_and_after_setting_new_position(self):
        # Normally, these are set when the movement is started.
        self.dev.startPosition = 0
        self.dev.movementStartTime = time.time()
        self.dev.targetPosition = 0

        self.assertEqual(self.dev.busy, False)
        target = 30
        self.dev.start_movement(target)
        self.assertEqual(self.dev.busy, True)
        self.dev.finalizeMovement()
        self.assertEqual(self.dev.busy, False)

    def test_that_movement_completion_works(self):
        self.dev.currentPosition = 0
        self.dev.targetPosition = 123.4

        self.dev.finalizeMovement()

        self.assertFalse(self.dev.busy)
        self.assertAlmostEqual(self.dev.targetPosition, self.dev.currentPosition, "not close enough", 0.1)

    def test_that_movement_takes_time(self):
        self.dev.currentPosition = 0
        timeItShouldTake = 0.8
        self.dev.speedInDegPerSecond = 100/timeItShouldTake

        self.dev.start_movement(100)
        time.sleep(timeItShouldTake * 0.5)  # Half the distance in half the time.
        self.dev.update()
        self.assertTrue(self.dev.busy)
        self.assertGreater(self.dev.currentPosition, 0)
        self.assertLess(self.dev.currentPosition, 95)