import time
import unittest

import behaviors.Axis


class OneAxis_tests(unittest.TestCase):
    def setUp(self):
        self.axis = behaviors.Axis.Axis('someName')

    def tearDown(self):
        pass

    def test_create_one_device(self):
        self.assertEqual(self.axis.name, 'someName')

    def test_that_it_has_limits(self):
        self.assertGreater(self.axis.limit_clockwise, self.axis.limit_anticlockwise)

    def test_busy_before_and_after_setting_new_position(self):
        # Normally, these are set when the movement is started.
        self.axis.startPosition = 0
        self.axis.movementStartTime = time.time()
        self.axis.targetPosition = 0

        self.assertEqual(self.axis.busy, False)
        target = 30
        self.axis.start_movement(target)
        self.assertEqual(self.axis.busy, True)
        self.axis.finalizeMovement()
        self.assertEqual(self.axis.busy, False)

    def test_that_movement_completion_works(self):
        self.axis.currentPosition = 0
        self.axis.targetPosition = 123.4

        self.axis.finalizeMovement()

        self.assertFalse(self.axis.busy)
        self.assertAlmostEqual(self.axis.targetPosition, self.axis.currentPosition, "not close enough", 0.1)

    def test_that_movement_takes_time(self):
        self.axis.currentPosition = 0
        timeItShouldTake = 0.8
        self.axis.speedInDegPerSecond = 100 / timeItShouldTake

        self.axis.start_movement(100)
        time.sleep(timeItShouldTake * 0.5)  # Half the distance in half the time.
        self.axis.update()
        self.assertTrue(self.axis.busy)
        self.assertGreater(self.axis.currentPosition, 0)
        self.assertLess(self.axis.currentPosition, 95)