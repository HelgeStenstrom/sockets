import socketInstrument
# import unittest
import unittest.mock
import sys
# from io import StringIO, BytesIO
# from argparse import ArgumentError


class Tests_with_print(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def qtestThatPrintoutsCanBeTested(self):
        print("some text", file=sys.stdout)
        self.assertIn("some text", sys.stdout.getvalue())
        print("some error", file=sys.stderr)
        self.assertIn("some error", sys.stderr.getvalue())


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

    def testMain1(self):

        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)
        # Denna metod failar, om den inte får Vt, Vc eller RotaryDisc som argument.
        # Annars så returnerar den aldrig. Den måste ha en separat tråd.

    def testPrinting(self):
        # Detta test fungerar bara med PyCharm, inte med stand-alone Python.
        # Det beror på att PyCharm implementerar stdout som en io.StringIO, men det görs inte av en naken Python.
        print("a string to be tested")
        self.assertIn("a string to be tested", sys.stdout.getvalue())



class rotary_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def testThatSomeSimpleComandsGetParsed(self):
        self.assertEqual(self.rd.matchOf("*IDN? "), socketInstrument.RotaryDiscBySocket.Idn)
        self.assertEqual(self.rd.matchOf("*OPT? "), socketInstrument.RotaryDiscBySocket.Options)
        self.assertEqual(self.rd.matchOf("CP"), "current position")
        self.assertEqual(self.rd.matchOf("  BU  ; "), socketInstrument.RotaryDiscBySocket.isBusy)


    def testThatParametrizedComandsGetParsed(self):
        self.assertEqual(self.rd.matchOf("LD -123.4 NP GO"), socketInstrument.RotaryDiscBySocket.startMovement, "negative fraction")
        self.assertEqual(self.rd.matchOf("LD 12.3 NP GO"), socketInstrument.RotaryDiscBySocket.startMovement, "postitive fraction")
        self.assertEqual(self.rd.matchOf("LD 12 NP GO"), socketInstrument.RotaryDiscBySocket.startMovement, "integer argument")
        #self.assertEqual(self.rd.matchOf("LD 12.3 NSP"), "set speed", "speed in deg per second")

    def testThatFaultyCommandsYieldsErrorMessage(self):
        self.assertEqual(self.rd.matchOf("unknown"), "no match")
        # self.assertEqual(self.rd.matchOf(" BU ; xx"), "no match")

class rotary_response_Tests(unittest.TestCase):
    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def testThatUnknownCommandReturnsErrorMessage(self):
        cmd = 'bad command'
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "error message")

    def testIdnReturnsIdentity(self):
        cmd = '*IDN?'
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "innco GmbH,CO3000,python,1.02.62")

    def testOptReturnsOptions(self):
        cmd = '*OPT?'
        response = self.rd.responseFunction(cmd)
        self.assertEqual(response, "AS1,DS1")

    def test_that_starting_movement_causes_busy(self):
        cmd = "LD -123.4 NP GO"
        self.assertEqual(self.rd.isBusy(), False)
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.isBusy(), True)

    def test_that_movement_goal_is_set(self):
        cmd = "LD -123.4 NP GO"
        self.rd.responseFunction(cmd)
        self.assertEqual(self.rd.targetPosition, -123.4)

class function_Tests(unittest.TestCase):
    def test_extraction_of_number_from_command(self):
        command = "LD -123.3 NP GO"
        number = socketInstrument.RotaryDiscBySocket.numberFromInncoCommand(None, command)
        self.assertEqual(number, -123.3)

class rotary_Functions_tests(unittest.TestCase):

    def setUp(self):
        self.rd = socketInstrument.RotaryDiscBySocket()

    def tearDown(self):
        pass

    def test_that_movement_completion_works(self):
        self.rd.position = 0
        self.rd.targetPosition = 123.4

        self.rd.finalizeMovement()

        self.assertFalse(self.rd.isBusy())
        self.assertAlmostEqual(self.rd.targetPosition, self.rd.position, "not close enough", 0.1)



class vötsch_response_Tests(unittest.TestCase):

    def setUp(self):
        self.v = socketInstrument.vötschBySocket()

    def testQuery(self):
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

    def testSetTempActual(self):
        self.v.setTempActual(17)
        response = self.v.responseFunction("$01I")
        tempString = response.split()[0]
        temp = float(tempString)
        self.assertEqual(17, temp)

    def testHelp(self):
        command = "$01?"
        response = self.v.responseFunction(command)
        self.assertTrue(response.startswith("ASCII"))

if __name__ == '__main__':
    unittest.main()
