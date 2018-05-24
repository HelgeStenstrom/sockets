import unittest

import socketInstrument


class ABBaseDemo_Tests(unittest.TestCase):
    def test_factory(self):
        a, b = socketInstrument.factoryMethod()
        self.assertIsInstance(a, socketInstrument.A)
        self.assertIsInstance(b, socketInstrument.Base)