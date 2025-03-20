"""
Sample tests
"""

from django.test import SimpleTestCase

from . import calc


class CalcTests(SimpleTestCase):
    """Test the calc module."""
    def test_add_numbers(self):
        """Test adding two numbers together."""
        res = calc.add(5, 6)
        self.assertEqual(res, 11)

    def test_add_string(self):
        """
            Test adding non integer values should be return zero.
            and print warning message.
        """
        res = calc.add('5', '6')
        self.assertEqual(res, 0)

    def test_substract_numbers(self):
        """Test subtracting two numbers together."""
        res = calc.subtract(10, 5)
        self.assertEqual(res, 5)
