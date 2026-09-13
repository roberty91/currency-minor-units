import unittest
from decimal import Decimal

from currency_minor_units import (
    decimal_to_minor_units,
    exponent_for,
    minor_units_to_decimal,
    minor_units_to_string,
)


class ExponentForTests(unittest.TestCase):
    def test_known_currency_is_case_insensitive(self):
        self.assertEqual(exponent_for("usd"), 2)
        self.assertEqual(exponent_for("USD"), 2)

    def test_zero_decimal_currency(self):
        self.assertEqual(exponent_for("JPY"), 0)

    def test_three_decimal_currency(self):
        self.assertEqual(exponent_for("BHD"), 3)

    def test_unknown_currency_raises(self):
        with self.assertRaises(KeyError):
            exponent_for("XXX")

    def test_four_decimal_currency(self):
        self.assertEqual(exponent_for("CLF"), 4)

    def test_non_decimal_subdivision_still_gets_two_places(self):
        # MGA and MRU subdivide into fifths, not tenths, but ISO 4217
        # assigns them 2 decimal digits and this library follows ISO.
        self.assertEqual(exponent_for("MGA"), 2)
        self.assertEqual(exponent_for("MRU"), 2)

    def test_newly_added_zero_decimal_currency(self):
        self.assertEqual(exponent_for("XOF"), 0)


class MinorUnitsToStringTests(unittest.TestCase):
    def test_usd(self):
        self.assertEqual(minor_units_to_string(1050, "USD"), "10.50")

    def test_jpy_has_no_decimal_point(self):
        self.assertEqual(minor_units_to_string(500, "JPY"), "500")

    def test_bhd_has_three_places(self):
        self.assertEqual(minor_units_to_string(1500, "BHD"), "1.500")

    def test_clf_has_four_places(self):
        self.assertEqual(minor_units_to_string(123456, "CLF"), "12.3456")

    def test_negative_amount(self):
        self.assertEqual(minor_units_to_string(-250, "USD"), "-2.50")

    def test_rejects_non_int(self):
        with self.assertRaises(TypeError):
            minor_units_to_string(10.5, "USD")


class DecimalToMinorUnitsTests(unittest.TestCase):
    def test_usd(self):
        self.assertEqual(decimal_to_minor_units("10.50", "USD"), 1050)

    def test_accepts_decimal_instance(self):
        self.assertEqual(decimal_to_minor_units(Decimal("10.50"), "USD"), 1050)

    def test_jpy_rejects_fractional_input(self):
        with self.assertRaises(ValueError):
            decimal_to_minor_units("10.5", "JPY")

    def test_rejects_extra_precision(self):
        with self.assertRaises(ValueError):
            decimal_to_minor_units("10.505", "USD")

    def test_rejects_float(self):
        with self.assertRaises(TypeError):
            decimal_to_minor_units(10.5, "USD")

    def test_rejects_garbage_string(self):
        with self.assertRaises(ValueError):
            decimal_to_minor_units("not a number", "USD")

    def test_round_trips_with_minor_units_to_decimal(self):
        original = 199
        as_decimal = minor_units_to_decimal(original, "USD")
        self.assertEqual(decimal_to_minor_units(as_decimal, "USD"), original)


if __name__ == "__main__":
    unittest.main()
