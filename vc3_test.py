import unittest

import Climate


class vc3_Tests(unittest.TestCase):
    def setUp(self):
        self.chamber = Climate.Vc37060()
        self.chamber.nominalTemp = 0
        self.chamber.actualTemperature = 0
        self.chamber.nominalHumidity = 0
        self.chamber.actualHumidity = 0
        self.chamber.fanSpeed = 0


    def test_command_string_finds_E_command(self):
        # Setup
        cmd = "$01E 0023.1 0000.0 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual("$01E", self.chamber.command)

    def test_command_string_finds_I_command(self):
        # Setup
        cmd = "$01I"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual("$01I", self.chamber.command)

    def test_set_Nominal_Temp(self):
        # Setup
        cmd = "$01E 0023.1 0000.0 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual(23.1, self.chamber.nominalTemp)

    def test_set_Nominal_Humidity(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0000.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual(87.1, self.chamber.nominalHumidity)

    def test_set_Fan_speed(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0080.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual(80, self.chamber.fanSpeed)

    def test_BitsAreCopied(self):
        # Setup
        cmd = "$01E 0023.1 0087.1 0080.0 0000.0 0000.0 0000.0 0000.0 " + 32*"0"

        # Exercise
        self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual(32 * "0", self.chamber.bits)

    def test_parts_of_E(self):
        # Setup

        # Execute
        response = self.chamber.responseFunction("$01I")
        parts = response.split()
        lastPart = parts[-1]

        # Verify
        # Number of values is 14 + 1
        self.assertEqual(15, len(parts))
        # Last value is a 32-bit binary number
        self.assertEqual(32, len(lastPart))

    def test_temp_humid_fan_of_E(self):
        # Setup
        self.chamber.nominalTemp = -12.3
        self.chamber.actualTemperature = 14.6
        self.chamber.nominalHumidity = 73.4
        self.chamber.actualHumidity = 72.1
        self.chamber.fanSpeed = 68.9

        # Execute
        response = self.chamber.responseFunction("$01I")
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
        # Setup
        cmd = self.cmd_for_set(32.1, 43.2, 67)

        # Exercise
        self.chamber.responseFunction(cmd)
        response = self.chamber.responseFunction("$01I")
        parts = response.split(" ")
        t = parts[0]
        h = parts[2]
        fs = parts[4]

        # Verify
        self.assertEqual("0032.1", t, "temperature read back")
        self.assertEqual("0043.2", h, "humidity setting read back")
        self.assertEqual("0067.0", fs, "fan speed read back")

    def test_accept_U_command(self):
        # Setup
        cmd = "$01U 0001.1 0000.0 0000.0 0000.0"
        # Execute
        response = self.chamber.responseFunction(cmd)

        # Verify
        self.assertEqual("0", response, "0 means OK")

    def test_has_ramped_setpoint_variables(self):

        # Exercise
        self.chamber.responseFunction(self.cmd_for_set(27))
        # Verify
        self.assertIsNotNone(self.chamber.currentWantedTemp, "variable that models wanted temperature setpoint")

    @unittest.skip("Test not done.")
    def qqtest_positive_temp_slope(self):
        # TODO: test ramping of temperature
        self.fail("TODO: ramping of temperature")

    # ---------------- Helper methods -----------------

    @staticmethod
    def cmd_for_set(temp, humidity=0.0, fanSpeed=50.0):
        """
        Form a set command
        :param temp: temperature
        :param humidity:
        :param fanSpeed:
        :return: command string including $01E
        """
        pp = [temp, humidity, fanSpeed] + 4 * [0]
        values = [Climate.VotschBase.decimal(part) for part in pp]
        parameters = " ".join(values) + " " + 32 * "0"
        cmd = "$01E %s" % parameters
        return cmd

    # -------------- Test helper methods -------------
    def test_help_cmd_for_set(self):
        actual = self.cmd_for_set(27)
        expected = "$01E 0027.0 0000.0 0050.0"
        self.assertEqual(expected, actual[:len(expected)], "same start of the command that contains the temperature")

    # No helpers at this time
