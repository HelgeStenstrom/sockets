import socketInstrument
# import unittest
import unittest.mock
import sys
# from io import StringIO, BytesIO
# from argparse import ArgumentError
import time

# TODO: läs http://stackoverflow.com/questions/31864168/mocking-a-socket-connection-in-python


class Tests_with_print(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_that_printouts_can_be_tested(self):
        print("some text", file=sys.stdout)
        self.assertIn("some text", sys.stdout.getvalue())
        print("some error", file=sys.stderr)
        self.assertIn("some error", sys.stderr.getvalue())

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

    def test_that_invalid_arguments_raises_SystemExit(self):

        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)
        # Denna metod failar, om den inte får Vt, Vc eller RotaryDisc som argument.
        # Annars så returnerar den aldrig. Den måste ha en separat tråd.

        # Test also with a valid offset
        sys.argv = ["", "--offset", "3.3", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)


class rotary_Tests(unittest.TestCase):
    # TODO: testa att offset och random fungerar som kommandots argument.
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass


    def test_that_devices_can_be_created(self):
        self.rd.attachedDevices = []
        self.rd.create_devices()
        devs = self.rd.attachedDevices
        names = [dev.name for dev in devs]
        self.assertListEqual(names, ['DS1', 'DS2'])

    def test_that_devices_are_created_on_init(self):
        devs = self.rd.attachedDevices
        names = [dev.name for dev in devs]
        self.assertListEqual(names, ['DS1', 'DS2'])

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

    def test_that_faulty_commands_yields_error_message(self):
        self.assertEqual(self.rd.commandFor("unknown"), None)

    def test_distance_function(self):
        limit = self.rd.farDistance
        self.assertTrue(self.rd.isDistant(limit+1))
        self.assertFalse(self.rd.isDistant(limit-1))


class rotary_response_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

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
        self.assertEqual(response, "AS1,DS1,DS2")

    def test_that_starting_movement_causes_busy(self):
        cmd = "LD -123.4 DG NP GO"
        self.assertEqual(self.rd.isBusy(), False)
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.isBusy(), True)

    def test_BU_response_before_and_after_setting_new_position(self):
        # Normally, these are set when the movement is started.
        self.rd.startPosition = 0
        self.rd.movementStartTime = time.time()
        self.rd.targetPosition = 0

        before = self.rd.responseFunction("BU")
        self.assertEqual(before, "0")
        self.rd.responseFunction("LD 123.4 DG NP GO")
        after = self.rd.responseFunction("BU")
        self.assertEqual(after, "1")
        self.rd.finalizeMovement()
        after2 = self.rd.responseFunction("BU")
        self.assertEqual(after2, "0")

    def test_that_movement_goal_is_set(self):
        cmd = "LD -123.4 DG NP GO"
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.targetPosition, -123.4)

    def test_that_movement_goal_is_returned(self):
        cmd = "LD -123.4 DG NP GO"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "-123.4")

    def test_that_current_position_is_returned(self):
        self.rd.movementStartTime = time.time()
        self.rd.targetPosition = -12.3
        self.rd.startPosition = -12.3
        self.rd.currentPosition = -12.3
        self.rd.speedInDegPerSecond = 3
        cmd = "CP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "-12.3")

    def test_that_the_speed_can_be_set(self):
        cmd = "LD 5.2 NSP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "5.2")
        self.assertEqual(self.rd.speedInDegPerSecond, 5.2)

    def test_that_speed_is_returned(self):
        self.rd.speedInDegPerSecond = 3.2
        cmd = "NSP"
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "3.2")

    def test_that_movement_takes_limited_time_and_reaches_target(self):
        self.rd.currentPosition = 0
        timeItShouldTake = 0.02
        self.rd.speedInDegPerSecond = 100/timeItShouldTake

        self.rd.responseFunction("LD 100 DG NP GO")
        response = self.rd.responseFunction("BU")
        self.assertEqual(response, "1")
        time.sleep(timeItShouldTake*1.3)  # Need to agree with slowDown in update function.
        response = self.rd.responseFunction("BU")
        self.assertNotEqual(self.rd.currentPosition, 0)
        self.assertEqual(response, "0")
        self.assertEqual(self.rd.currentPosition, 100)

    def test_that_movement_takes_time(self):
        self.rd.currentPosition = 0
        timeItShouldTake = 0.08
        self.rd.speedInDegPerSecond = 100/timeItShouldTake

        self.rd.responseFunction("LD 100 DG NP GO")
        time.sleep(timeItShouldTake * 0.5)  # Half the distance in half the time.
        response = self.rd.responseFunction("CP")
        self.assertNotEqual(response, "0")
        self.assertGreater(self.rd.currentPosition, 0)
        self.assertLess(self.rd.currentPosition, 95)


class function_Tests(unittest.TestCase):
    def test_extraction_of_number_from_command(self):
        command = "LD -123.3 DG NP GO"
        number = socketInstrument.RotaryDiscBySocket.numberFromInncoCommand(command)
        self.assertEqual(number, -123.3)


class rotary_Functions_tests(unittest.TestCase):

    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_movement_completion_works(self):
        self.rd.currentPosition = 0
        self.rd.targetPosition = 123.4

        self.rd.finalizeMovement()

        self.assertFalse(self.rd.isBusy())
        self.assertAlmostEqual(self.rd.targetPosition, self.rd.currentPosition, "not close enough", 0.1)


class OneRotaryDisc_tests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_one_device(self):
        dev = socketInstrument.OneRotaryDisc('someName')
        self.assertEqual(dev.name, 'someName')

    def QQtest_that_it_has_limits(self):
        raise NotImplementedError


class vötsch_response_Tests(unittest.TestCase):

    def setUp(self):
        self.v = socketInstrument.vötschBySocket()

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

if __name__ == '__main__':
    unittest.main()
