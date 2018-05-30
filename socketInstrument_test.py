import Amplifier
import Robotics
import socketInstrument
import unittest
import sys
import socketMain


# TODO: läs http://stackoverflow.com/questions/31864168/mocking-a-socket-connection-in-python


@unittest.skip("Skipping tests that print.")
class Tests_with_print(unittest.TestCase):
    # TODO: Find out how to test printouts in PyCharm + Python 3.6, both Mac and Windows
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # @unittest.skip("Vill inte ha utskrifter till konsolen.")
    def test_that_printouts_can_be_tested(self):
        print("some text", file=sys.stdout)
        self.assertIn("some text", sys.stdout.getvalue())
        print("some error", file=sys.stderr)
        self.assertIn("some error", sys.stderr.getvalue())

    # @unittest.skip("Vill inte ha utskrifter till konsolen.")
    def test_printing(self):
        # Detta test fungerar bara med PyCharm, inte med stand-alone Python.
        # Det beror på att PyCharm implementerar stdout som en io.StringIO, men det görs inte av en naken Python.
        tested = "a string to be tested"
        print(tested)
        self.assertIn(tested, sys.stdout.getvalue())


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

    # @unittest.skip("Prints to screen, and I don't want that.")
    def test_that_invalid_arguments_raises_SystemExit(self):

        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketMain.main)
        # Denna metod failar, om den inte får Vt, Vc eller RotaryDisc som argument.
        # Annars så returnerar den aldrig. Den måste ha en separat tråd.

        # Test also with a valid offset
        sys.argv = ["", "--offset", "3.3", "Invalid_argument"]
        self.assertRaises(SystemExit, socketMain.main)

    # @unittest.skip("Prints to screen, and I don't want that.")
    def test_that_invalid_arguments_raises_SystemExit_in_function(self):
        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketMain.instrumentTypeArgument)

    def test_cmd_line_argument_RotaryDisc(self):
        sys.argv = ["", "RotaryDisc"]
        instrument = socketMain.instrumentTypeArgument()
        self.assertIsInstance(instrument, Robotics.RotaryDiscBySocket)

    def test_cmd_line_argument_Empower(self):
        sys.argv = ["", "Empower"]
        instrument = socketMain.instrumentTypeArgument()
        self.assertIsInstance(instrument, Amplifier.PaEmpower)

    def test_cmd_line_argument_Optimus(self):
        sys.argv = ["", "Optimus"]
        instrument = socketMain.instrumentTypeArgument()
        self.assertIsInstance(instrument, Robotics.Optimus)


class function_Tests(unittest.TestCase):
    def test_extraction_of_number_from_command(self):
        command = "LD -123.3 DG NP GO"
        number = Robotics.RotaryDiscBySocket.numberFromInncoCommand(command)
        self.assertEqual(number, -123.3)

    def test_prettyprinting_nonprints(self):
        sample = ".\n.\r."
        expected = ".<LF>.<CR>."
        actual = socketInstrument.toPrintable(sample)
        self.assertEqual(actual, expected)


class AntennaStandTests(unittest.TestCase):
    def setUp(self):
        self.dev = Robotics.AntennaStand("someName")

    def test_create_one_device(self):
        self.assertEqual(self.dev.name, 'someName')

    def test_setting_polarization(self):
        self.dev.setPolarization("V")
        self.assertEqual(self.dev.getPolarization(), "V")


if __name__ == '__main__':
    unittest.main()
