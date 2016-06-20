import votschSocket
import unittest
import socketserver
import socket
#import unittest.mock
import sys
from io import StringIO


class handler_Tests(unittest.TestCase):
    def testPass(self):
        pass
    def qtest1(self):
        """Set up basic communication with socket server"""
        HOST, PORT = 'localhost', 9999
        # Create the server, binding to localhost on port 9999
        server = socketserver.TCPServer((HOST, PORT), votschSocket.MyTCPHandler)
        server.server_activate()
        #server.serve_forever()
        #print("test1 started")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            sock.sendall(b"my message")

            r = sock.recv(1024)
            print("type(r) == ", type(r))
            #received = str(r, "utf-8")

        self.assertEqual(r, "my message")


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


if __name__ == "__main__":
    unittest.main()