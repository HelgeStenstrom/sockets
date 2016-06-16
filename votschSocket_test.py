import votschSocket
import unittest
import unittest.mock
import sys
from io import StringIO


class main_Tests(unittest.TestCase):

    def setUp(self):
        self.v = votschSocket.vötschFake()
        self.stdout = StringIO()
        sys.stdout = self.stdout


    def tearDown(self):
        sys.stdout = sys.__stdout__


    def testSkriv(self):
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
        self.v = votschSocket.vötschFake()

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

