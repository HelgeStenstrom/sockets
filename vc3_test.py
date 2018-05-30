import unittest

import Climate
import socketInstrument


class vc3_Tests(unittest.TestCase):
    def setUp(self):
        self.v = Climate.Vc37060()
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

    @unittest.skip("Test not done.")
    def test_set_read_roundtrip(self):
        #TODO: Set nominal values and read them back
        self.fail("TODO: Set nominal values and read them back")

    @unittest.skip("Test not done.")
    def test_positive_temp_slope(self):
        # TODO: ramping of temperature
        self.fail("TODO: ramping of temperature")

    # ---------------- Helper methods -----------------
    # -------------- Test helper methods -------------

    # No helpers at this time