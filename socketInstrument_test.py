import socketInstrument
import unittest
import sys
import time

# TODO: läs http://stackoverflow.com/questions/31864168/mocking-a-socket-connection-in-python


@unittest.skip("Skipping tests that print.")
class Tests_with_print(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("Vill inte ha utskrifter till konsolen.")
    def test_that_printouts_can_be_tested(self):
        print("some text", file=sys.stdout)
        self.assertIn("some text", sys.stdout.getvalue())
        print("some error", file=sys.stderr)
        self.assertIn("some error", sys.stderr.getvalue())

    @unittest.skip("Vill inte ha utskrifter till konsolen.")
    def test_printing(self):
        # Detta test fungerar bara med PyCharm, inte med stand-alone Python.
        # Det beror på att PyCharm implementerar stdout som en io.StringIO, men det görs inte av en naken Python.
        print("a string to be tested")
        self.assertIn("a string to be tested", sys.stdout.getvalue())


class main_Tests(unittest.TestCase):

    def setUp(self):

        # Försök att undvika utskrift. Verkar inte fungera i PyCharm, troligen för att miljön kräver stdout.
        # Kanske det finns andra sätt i denna miljö.
        # sys.stdout = StringIO()
        # sys.stderr = StringIO()
        pass

    def tearDown(self):
        # sys.stdout = sys.__stdout__
        # sys.stderr = sys.__stderr__
        # help(sys.stderr)
        pass

    @unittest.skip("Prints to screen, and I don't want that.")
    def test_that_invalid_arguments_raises_SystemExit(self):

        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)
        # Denna metod failar, om den inte får Vt, Vc eller RotaryDisc som argument.
        # Annars så returnerar den aldrig. Den måste ha en separat tråd.

        # Test also with a valid offset
        sys.argv = ["", "--offset", "3.3", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)

    @unittest.skip("Prints to screen, and I don't want that.")
    def test_that_invalid_arguments_raises_SystemExit_in_function(self):
        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.instrumentTypeArgument)

    def test_cmd_line_argument_RotaryDisc(self):
        sys.argv = ["", "RotaryDisc"]
        instrument = socketInstrument.instrumentTypeArgument()
        self.assertIsInstance(instrument, socketInstrument.RotaryDiscBySocket)

    def test_cmd_line_argument_Empower(self):
        sys.argv = ["", "Empower"]
        instrument = socketInstrument.instrumentTypeArgument()
        self.assertIsInstance(instrument, socketInstrument.PaEmpower)

    def test_cmd_line_argument_Optimus(self):
        sys.argv = ["", "Optimus"]
        instrument = socketInstrument.instrumentTypeArgument()
        self.assertIsInstance(instrument, socketInstrument.Optimus)



class rotary_Tests(unittest.TestCase):
    # TODO: testa att offset och random fungerar som kommandots argument.
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_devices_have_names(self):
        devs = self.rd.attachedDevices
        names = [dev.name for dev in devs]
        self.assertListEqual(names, self.rd.devNamesToAttach)

    def test_that_some_simple_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("*IDN? "), socketInstrument.RotaryDiscBySocket.Idn_response)
        self.assertEqual(self.rd.commandFor("*OPT? "), socketInstrument.RotaryDiscBySocket.OPT_response)
        self.assertEqual(self.rd.commandFor("CP  "), socketInstrument.RotaryDiscBySocket.CP_response)
        self.assertEqual(self.rd.commandFor("BU  ; "), socketInstrument.RotaryDiscBySocket.BU_Response)

    def test_that_parametrized_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("LD -123.4 DG NP GO"),
                         socketInstrument.RotaryDiscBySocket.LD_NP_GO_response, "negative fraction")
        self.assertEqual(self.rd.commandFor("LD 12.3 DG NP GO"),
                         socketInstrument.RotaryDiscBySocket.LD_NP_GO_response, "postitive fraction")
        self.assertEqual(self.rd.commandFor("LD 12 DG NP GO"),
                         socketInstrument.RotaryDiscBySocket.LD_NP_GO_response, "integer argument")
        self.assertEqual(self.rd.commandFor("LD 12.3 NSP"),
                         socketInstrument.RotaryDiscBySocket.LD_NSP_response, "speed in deg per second")
        self.assertEqual(self.rd.commandFor("NSP"),
                         socketInstrument.RotaryDiscBySocket.NSP_response, "Returned speed")
        self.assertEqual(self.rd.commandFor("LD DS2 DV"),
                         socketInstrument.RotaryDiscBySocket.LD_dev_DV_response, "Select current device")

    def test_distance_function(self):
        limit = self.rd.farDistance
        self.assertTrue(self.rd.isDistant(limit+1))
        self.assertFalse(self.rd.isDistant(limit-1))


class rotary_response_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()
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
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_a_device_can_be_found_by_name(self):
        devs = self.rd.attachedDevices
        devsByName = [self.rd.deviceByName(n) for n in self.rd.devNamesToAttach]
        self.assertEqual(devs, devsByName)


class Rotary_command_tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_LD_DV_command_is_parsed(self):
        pass

    def test_that_a_device_is_selected(self):
        cmd = "LD DS2 DV"
        self.rd.responseFunction(cmd)
        # TODO: Kolla att DS1 blir current device
        self.assertEqual(self.rd.currentDevice, self.rd.deviceByName('DS2'))


class Ncd_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.MaturoNCD()

    def tearDown(self):
        pass

    def test_that_some_simple_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("*IDN? "), socketInstrument.MaturoNCD.Idn_response)
        self.assertEqual(self.rd.commandFor("CP  "), socketInstrument.MaturoNCD.CP_response)
        self.assertEqual(self.rd.commandFor("BU  ; "), socketInstrument.MaturoNCD.BU_Response)

    def test_that_parametrized_commands_get_parsed(self):
        self.assertEqual(self.rd.commandFor("LD -123.4 DG NP GO"),
                         socketInstrument.MaturoNCD.LD_NP_GO_response, "negative fraction")
        self.assertEqual(self.rd.commandFor("LD 12.3 DG NP GO"),
                         socketInstrument.MaturoNCD.LD_NP_GO_response, "postitive fraction")
        self.assertEqual(self.rd.commandFor("LD 12 DG NP GO"),
                         socketInstrument.MaturoNCD.LD_NP_GO_response, "integer argument")
        self.assertEqual(self.rd.commandFor("LD 7 SP"),
                         socketInstrument.MaturoNCD.LD_SP_response, "speed on 1-8 scale")
        self.assertEqual(self.rd.commandFor("SP"),
                         socketInstrument.MaturoNCD.SP_response, "Returned speed")
        self.assertEqual(self.rd.commandFor("LD 1 DV"),
                         socketInstrument.MaturoNCD.LD_dev_DV_response, "Select current device")


class Ncd_response_FrontDoor_Tests(unittest.TestCase):
    def setUp(self):
        self.ncd = socketInstrument.MaturoNCD()
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
        self.ncd = socketInstrument.MaturoNCD()
        rotDevices = [dev for dev in self.ncd.attachedDevices if isinstance(dev, socketInstrument.OneRotaryDisc)]
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
        cd.speedInDegPerSecond = 100/timeItShouldTake

        self.ncd.responseFunction("LD 100 DG NP GO")
        response = self.ncd.responseFunction("BU")
        self.assertEqual(response, "1")
        time.sleep(timeItShouldTake*1.3)  # Need to agree with slowDown in update function.
        response = self.ncd.responseFunction("BU")
        self.assertNotEqual(cd.currentPosition, 0)
        self.assertEqual(response, "0")
        self.assertEqual(cd.currentPosition, 100)

    def test_that_movement_takes_time(self):
        cd = self.ncd.currentDevice
        cd.currentPosition = 0
        timeItShouldTake = 0.08
        cd.speedInDegPerSecond = 100/timeItShouldTake

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
        self.ncd = socketInstrument.MaturoNCD()
        self.ncd.currentDevice = self.ncd.deviceByName("0")
        self.assertIsInstance(self.ncd.currentDevice, socketInstrument.AntennaStand)

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
        self.assertIsInstance(antennaStand, socketInstrument.AntennaStand, "we need an AntennaStand for the test")

        self.ncd.currentDevice = antennaStand
        response = self.ncd.responseFunction("SP?")
        self.assertEqual(response, "E - V")

    def test_pol_command_on_rotary_disc(self):
        ttDevice = self.ncd.deviceByName("1")
        # Precondition
        self.assertIsInstance(ttDevice, socketInstrument.OneRotaryDisc, "we need a OneRotaryDisc for the test")

        self.ncd.currentDevice = ttDevice
        response = self.ncd.responseFunction("P?")
        self.assertEqual(response, "E - V")
        response = self.ncd.responseFunction("PH")
        self.assertEqual(response, "E - V")
        response = self.ncd.responseFunction("PV")
        self.assertEqual(response, "E - V")



class Ncd_top_level_function_tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.MaturoNCD()

    def tearDown(self):
        pass

    def test_that_a_device_can_be_found_by_name(self):
        devs = self.rd.attachedDevices
        devsByName = [self.rd.deviceByName(n) for n in self.rd.devNamesToAttach]
        self.assertEqual(set(devs), set(devsByName))


class function_Tests(unittest.TestCase):
    def test_extraction_of_number_from_command(self):
        command = "LD -123.3 DG NP GO"
        number = socketInstrument.RotaryDiscBySocket.numberFromInncoCommand(command)
        self.assertEqual(number, -123.3)

    def test_prettyprinting_nonprints(self):
        sample = ".\n.\r."
        expected = ".<LF>.<CR>."
        actual = socketInstrument.prettify(sample)
        self.assertEqual(actual, expected)


class OptimusTests(unittest.TestCase):
    def setUp(self):
        self.box = socketInstrument.Optimus()

    # TODO: Update to status format "sensorPower, motorPower, x (xStatus), y (yStatus), phi (phiStatus), theta (thetaStatus)"
    # "7, 8, 12.23 (11), 22.12 (22), 32.12 (33), 42.2 (44)"

    def test_that_status_returns_positions(self):
        (self.box.x, self.box.y, self.box.phi, self.box.theta) = (11, 12, 13, 14)
        # TODO: Check only the interesting parts, not the whole string.
        expectedStatus = "0, 0, 11.0 (0), 12.0 (0), 13.0 (0), 14.0 (0)"
        response = self.box.responseFunction("status")
        self.assertEqual(expectedStatus, response)

    def test_that_zero_cmd_sets_zero_internally(self):
        self.box.responseFunction("mv_to_zero")
        self.assertEqual((self.box.x, self.box.y, self.box.phi, self.box.theta),
                         (0, 0, 0, 0))


    def test_that_zero_cmd_sets_zero(self):
        self.box.responseFunction("mv_to_zero")
        response = self.box.responseFunction("status")
        self.assertEqual(response, "0, 0, 0.0 (0), 0.0 (0), 0.0 (0), 0.0 (0)")

    # TODO: Update commands to rotate_phi, rotate_theta, move_x, move_y

    def test_that_move_x_moves(self):
        self.box.responseFunction("move_x_to -12.3")
        self.assertEqual(-12.3, self.box.x)

    def test_that_move_y_moves(self):
        self.box.responseFunction("move_y_to 22")
        self.assertEqual(22, self.box.y)

    def test_that_rotate_phi_rotates(self):
        self.box.responseFunction("rotate_phi_to 33")
        self.assertEqual(33, self.box.phi)

    def test_that_rotate_theta_rotates(self):
        self.box.responseFunction("rotate_theta_to 44")
        self.assertEqual(44, self.box.theta)

    def test_that_bad_commands_get_nack(self):
        response = self.box.responseFunction("bad commmand")
        self.assertEqual("nack", response)


class rotary_Functions_tests(unittest.TestCase):

    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

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
        self.dev = socketInstrument.OneRotaryDisc('someName')

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


class AntennaStandTests(unittest.TestCase):
    def setUp(self):
        self.dev = socketInstrument.AntennaStand("someName")

    def test_create_one_device(self):
        self.assertEqual(self.dev.name, 'someName')

    def test_setting_polarization(self):
        self.dev.setPolarization("V")
        self.assertEqual(self.dev.getPolarization(), "V")


class votsch_response_Tests(unittest.TestCase):

    def setUp(self):
        self.v = socketInstrument.votschBase()

    def test_most_parts_of_a_query(self):
        command = "$01I"
        response = self.v.responseFunction(command)
        parts = response.split()

        self.assertEqual(len(parts), 15)
        binaryParts = parts[-1]
        self.assertEqual(len(binaryParts), 32)

        floatParts = parts[:-1]
        for part in floatParts:
            self.assertEqual(len(part), 6)
            self.assertEqual(part[-2], '.')

        for d in binaryParts:
            self.assertTrue(d in "01")

        self.assertTrue(response.startswith("0027.1"))
        # TODO: don't be dependent on defaults in the vötsch __init__ method.

    def test_that_the_actual_temperature_can_be_set_and_read(self):
        self.v.setTempActual(-17.3)
        response = self.v.responseFunction("$01I")
        tempString = response.split()[0]
        temp = float(tempString)
        self.assertEqual(-17.3, temp)
        self.assertEqual("-017.3", tempString)
        # TODO: Check with an actual Vötsch, that the temperature field looks like above.

    def test_the_response_to_the_help_command(self):
        command = "$01?"
        response = self.v.responseFunction(command)
        # TODO: check what the actual response of a Vötsch is, and test for that instead.
        self.assertTrue(response.startswith("ASCII"))

class vc3_Tests(unittest.TestCase):
    def setUp(self):
        self.v = socketInstrument.Vc37060()
        self.v.nominalTemp = 0
        self.v.actualTemperature = 0
        self.v.nominalHumidity = 0
        self.v.actualHumidity = 0
        self.v.fanSpeed = 0


    def test_command_string_finds_E_command(self):
        # Setup
        cmd = "$01E 0023.1 0000.0 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual("$01E", self.v.command)

    def test_command_string_finds_I_command(self):
        # Setup
        cmd = "$01I"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual("$01I", self.v.command)

    def test_set_Nominal_Temp(self):
        # Setup
        cmd = "$01E 0023.1 0000.0 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual(23.1, self.v.nominalTemp)

    def test_set_Nominal_Humidity(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual(87.1, self.v.nominalHumidity)

    def test_set_Fan_speed(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0080.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual(80, self.v.fanSpeed)

    def test_BitsAreCopied(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0080.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.v.responseFunction(cmd)

        # Verify
        self.assertEqual(32*"0", self.v.bits)

    def test_parts_of_E(self):
        # Setup

        # Execute
        response = self.v.responseFunction("$01I")
        parts = response.split()
        lastPart = parts[-1]

        # Verify
        # Number of values is 14 + 1
        self.assertEqual(15, len(parts))
        # Last value is a 32-bit binary number
        self.assertEqual(32, len(lastPart))

    def test_temp_humid_fan_of_E(self):
        # Setup
        self.v.nominalTemp =-12.3
        self.v.actualTemperature = 14.6
        self.v.nominalHumidity = 73.4
        self.v.actualHumidity = 72.1
        self.v.fanSpeed = 68.9

        # Execute
        response = self.v.responseFunction("$01I")
        parts = response.split()
        lastPart = parts[-1]

        # Verify
        self.assertEqual("-012.3", parts[0])
        self.assertEqual("0014.6", parts[1])
        self.assertEqual("0073.4", parts[2])
        self.assertEqual("0072.1", parts[3])
        self.assertEqual("0068.9", parts[4], "fanspeed")

        self.assertEqual(32*'0', lastPart)

    def test_set_read_roundtrip(self):
        #TODO: Set nominal values and read them back
        self.fail("TODO: Set nominal values and read them back")

    def test_positive_temp_slope(self):
        # TODO: ramping of temperature
        self.fail("TODO: ramping of temperature")

    # ---------------- Helper methods -----------------
    # -------------- Test helper methods -------------

    # No helpers at this time


if __name__ == '__main__':
    unittest.main()
