import socketInstrument
import unittest
import unittest.mock
import sys
from io import StringIO, BytesIO
from argparse import ArgumentError

# Idé: jag vill ha ett beteende som kan pluggas i, så att jag lätt kan simulera olika instrument.
# Lätt byta mellan Vötsch och ett SCPI-instrument.
# Därmed ändras Vötsch till ett allmänt instrumnt, och olika instrument har olika response-funktioner.

class main_Tests(unittest.TestCase):

    def qsetUp(self):

        # Försök att undvika utskrift. Verkar inte fungera i PyCharm, troligen för att miljön kräver stdout.
        # Kanske det finns andra sätt i denna miljö.
        #sys.stdout = StringIO()
        #sys.stderr = StringIO()
        pass

    def tearDown(self):
        #sys.stdout = sys.__stdout__
        #sys.stderr = sys.__stderr__
        pass

    def testMain1(self):

        sys.argv = ["", "Invalid_argument"]
        self.assertRaises(SystemExit, socketInstrument.main)
        # Denna metod failar, om den inte får Vt, Vc eller RotaryDisc som argument.
        # Annars så returnerar den aldrig. Den måste ha en separat tråd.


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
