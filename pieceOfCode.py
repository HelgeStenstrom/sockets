<<<<<<< HEAD
class otherTests(unittest.TestCase):
    def test_embedded_eol(self):
        # Setup
        longstring = """
a
b
c
        """

        # Exercise
        pieces = longstring.splitlines()
        changed = "\r\n".join(pieces)

        # Expected

        self.assertIn('a\nb\nc', longstring)

        self.assertIn('a\r\nb\r\nc', changed)
=======
