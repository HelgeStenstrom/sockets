import votschSocket
import unittest
import unittest.mock
import sys
from io import StringIO

# Idé: jag vill ha ett beteende som kan pluggas i, så att jag lätt kan simulera olika instrument.
# Lätt byta mellan Vötsch och ett SCPI-instrument.
# Därmed ändras Vötsch till ett allmänt instrumnt, och olika instrument har olika response-funktioner.

class main_Tests(unittest.TestCase):

    def setUp(self):
        self.v = votschSocket.vötschBySocket()
        self.stdout = StringIO()
        sys.stdout = self.stdout


    def tearDown(self):
        sys.stdout = sys.__stdout__


    def testSkriv(self):
        "Utskrifter kan testas"
        print("hej")

        self.assertEqual(self.stdout.getvalue().strip(), "hej")
        self.assertTrue(self.stdout.getvalue().startswith("hej"))


    def testPrint(self):
        command = "$01I"
        response = self

    def testMain1(self):
        #m = votschSocket.main()
        print("Success")
        self.assertTrue(self.stdout.getvalue().startswith("Success"))


class response_Tests(unittest.TestCase):

    def setUp(self):
        self.v = votschSocket.vötschBySocket()

    def testQuery(self):
        command = "$01I"
        response = self.v.responseFunction(command)
        parts = response.split()

        self.assertEqual(len(parts), 17)
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
