import unittest

import Robotics
import socketInstrument


class OptimusTests(unittest.TestCase):
    def setUp(self):
        self.box = Robotics.Optimus()

    # TODO: Update to status format "sensorPower, motorPower, x (xStatus), y (yStatus), phi (phiStatus), theta (thetaStatus)"
    # "7, 8, 12.23 (11), 22.12 (22), 32.12 (33), 42.2 (44)"

    def test_that_status_returns_positions(self):
        (self.box.x, self.box.y, self.box.phi, self.box.theta) = (11, 12, 13, 14)
        # TODO: Check only the interesting parts, not the whole string.
        expectedStatus = "0, 0, 11.0 (0), 12.0 (0), 13.0 (0), 14.0 (0)"
        response = self.box.responseFunction("status")
        self.assertEqual(expectedStatus, response)

    def test_that_zero_cmd_sets_zero_internally(self):
        self.box.responseFunction("mv_to_zero")
        self.assertEqual((self.box.x, self.box.y, self.box.phi, self.box.theta),
                         (0, 0, 0, 0))


    def test_that_zero_cmd_sets_zero(self):
        self.box.responseFunction("mv_to_zero")
        response = self.box.responseFunction("status")
        self.assertEqual(response, "0, 0, 0.0 (0), 0.0 (0), 0.0 (0), 0.0 (0)")

    # TODO: Update commands to rotate_phi, rotate_theta, move_x, move_y

    def test_that_move_x_moves(self):
        self.box.responseFunction("move_x_to -12.3")
        self.assertEqual(-12.3, self.box.x)

    def test_that_move_y_moves(self):
        self.box.responseFunction("move_y_to 22")
        self.assertEqual(22, self.box.y)

    def test_that_rotate_phi_rotates(self):
        self.box.responseFunction("rotate_phi_to 33")
        self.assertEqual(33, self.box.phi)

    def test_that_rotate_theta_rotates(self):
        self.box.responseFunction("rotate_theta_to 44")
        self.assertEqual(44, self.box.theta)

    def test_that_bad_commands_get_nack(self):
        response = self.box.responseFunction("bad commmand")
        self.assertEqual("nack", response)