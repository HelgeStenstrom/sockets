import unittest

import Climate


class votsch_response_Tests(unittest.TestCase):
    def setUp(self):
        self.chamber = Climate.VotschBase()

    def test_most_parts_of_a_query(self):
        self.chamber.actualTemperature = 13.4
        command = "$01I"
        response = self.chamber.responseFunction(command)
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

        self.assertEqual(13.4, float(parts[1]), "Actual temperature read back")

    def test_that_the_actual_temperature_can_be_set_and_read(self):
        self.chamber.setTempActual(-17.3)
        response = self.chamber.responseFunction("$01I")
        tempString = response.split()[1]
        temp = float(tempString)
        self.assertEqual(-17.3, temp)
        self.assertEqual("-017.3", tempString)

    def test_the_response_to_the_help_command(self):
        command = "$01?"
        response = self.chamber.responseFunction(command)
        # TODO: check what the actual response of a Vötsch is, and test for that instead.
        self.assertTrue(response.startswith("ASCII"))

    def test_that_U_sets__temperature_slope_up(self):
        # Setup
        command = "$01U 001.2 000.0 000.0 000.0"

        # Exercise
        response = self.chamber.responseFunction(command)

        # Verify
        self.assertEqual("0", response, "Return 0 if command accepted")
        self.assertEqual(1.2, self.chamber.tempUp, "The upward slope variable")
        self.assertEqual(0, self.chamber.tempDown, "The downward slope variable")

    def test_that_U_sets_slopes_down(self):
        # Setup
        command = "$01U 0000.0 0001.3 0000.0 0002.2"

        # Exercise
        response = self.chamber.responseFunction(command)

        # Verify
        self.assertEqual("0", response, "Return 0 if command accepted")
        self.assertEqual(0, self.chamber.tempUp, "The upward slope variable")
        self.assertEqual(1.3, self.chamber.tempDown, "The downward temp slope variable")
        self.assertEqual(2.2, self.chamber.humDown, "The downward humidity slope variable")

    def test_that_overspecified_U_is_error(self):
        # Setup
        command = "$01U 0001.1 0001.3 0000.0 0000.0"

        # Exercise
        response = self.chamber.responseFunction(command)

        # Verify
        self.assertEqual("", response, "Return empty string if command not accepted")

    def test_U_with_parse_error(self):
        # Setup
        command = "$01U sfd.1 sdf.3 sdf.0 sfd.0"

        # Exercise
        response = self.chamber.responseFunction(command)

        # Verify
        self.assertEqual("", response, "Return empty string if command not accepted")

    def QQQtest_that_U_starts_rampStartValues(self):
        # Setup
        command = "$01U 0000.0 0001.3 0000.0 0002.2"

        # Exercise
        response = self.chamber.responseFunction(command)

        # Verify
        self.fail("Test not done")
