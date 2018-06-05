import unittest

import Climate


class votsch_response_Tests(unittest.TestCase):
    # TODO: Move to climate_test
    def setUp(self):
        self.chamber = Climate.VotschBase()

    def test_most_parts_of_a_query(self):
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

        self.assertTrue(response.startswith("0027.1"))
        # TODO: don't be dependent on defaults in the vötsch __init__ method.

    def test_that_the_actual_temperature_can_be_set_and_read(self):
        self.chamber.setTempActual(-17.3)
        response = self.chamber.responseFunction("$01I")
        tempString = response.split()[0]
        temp = float(tempString)
        self.assertEqual(-17.3, temp)
        self.assertEqual("-017.3", tempString)
        # TODO: Check with an actual Vötsch, that the temperature field looks like above.

    def test_the_response_to_the_help_command(self):
        command = "$01?"
        response = self.chamber.responseFunction(command)
        # TODO: check what the actual response of a Vötsch is, and test for that instead.
        self.assertTrue(response.startswith("ASCII"))
