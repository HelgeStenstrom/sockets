import socketInstrument
import unittest
import sys


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


if __name__ == '__main__':
    unittest.main()
