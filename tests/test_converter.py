import unittest
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from currency_minor_units import (
    convert_minor_units,
    decimal_to_minor_units,
    exponent_for,
    formatted_string_to_minor_units,
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


class FormattedStringToMinorUnitsTests(unittest.TestCase):
    def test_dollar_sign_with_thousands_separator(self):
        self.assertEqual(formatted_string_to_minor_units("$1,050.00", "USD"), 105000)

    def test_symbol_after_amount_with_space(self):
        self.assertEqual(formatted_string_to_minor_units("1050.00 $", "USD"), 105000)

    def test_european_style_separators(self):
        self.assertEqual(formatted_string_to_minor_units("1.050,00", "EUR"), 105000)

    def test_plain_amount_no_separators(self):
        self.assertEqual(formatted_string_to_minor_units("10.50", "USD"), 1050)

    def test_currency_code_prefix(self):
        self.assertEqual(formatted_string_to_minor_units("USD 10.50", "USD"), 1050)

    def test_currency_code_suffix(self):
        self.assertEqual(formatted_string_to_minor_units("10.50 USD", "USD"), 1050)

    def test_zero_decimal_currency_with_grouping(self):
        self.assertEqual(formatted_string_to_minor_units("JPY 1,050", "JPY"), 1050)

    def test_parentheses_mean_negative(self):
        self.assertEqual(formatted_string_to_minor_units("(10.50)", "USD"), -1050)

    def test_leading_minus_sign(self):
        self.assertEqual(formatted_string_to_minor_units("-$10.50", "USD"), -1050)

    def test_sign_between_symbol_and_digits(self):
        self.assertEqual(formatted_string_to_minor_units("$-10.50", "USD"), -1050)

    def test_leading_plus_sign(self):
        self.assertEqual(formatted_string_to_minor_units("+10.50", "USD"), 1050)

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(formatted_string_to_minor_units("  10.50  ", "USD"), 1050)

    def test_lowercase_currency_code_is_accepted(self):
        self.assertEqual(formatted_string_to_minor_units("usd 10.50", "USD"), 1050)

    def test_multiple_thousands_groups(self):
        self.assertEqual(
            formatted_string_to_minor_units("$1,234,567.89", "USD"), 123456789
        )

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            formatted_string_to_minor_units(1050, "USD")

    def test_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            formatted_string_to_minor_units("", "USD")

    def test_rejects_symbol_only_string(self):
        with self.assertRaises(ValueError):
            formatted_string_to_minor_units("$", "USD")

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            formatted_string_to_minor_units("not an amount", "USD")


class ConvertMinorUnitsTests(unittest.TestCase):
    def test_exact_conversion(self):
        self.assertEqual(convert_minor_units(1000, "EUR", "USD", "1.08"), 1080)

    def test_rounds_half_up_by_default(self):
        # 3.33 EUR * 1.005 = 3.34665, which rounds to 3.35 USD.
        self.assertEqual(convert_minor_units(333, "EUR", "USD", "1.005"), 335)

    def test_rounding_mode_is_configurable(self):
        self.assertEqual(
            convert_minor_units(333, "EUR", "USD", "1.005", rounding=ROUND_DOWN),
            334,
        )

    def test_converts_to_zero_decimal_currency(self):
        # 3.33 USD * 150.4 = 500.832, rounds to 501 whole yen.
        self.assertEqual(convert_minor_units(333, "USD", "JPY", "150.4"), 501)

    def test_accepts_decimal_rate(self):
        self.assertEqual(convert_minor_units(1000, "EUR", "USD", Decimal("1.08")), 1080)

    def test_rejects_float_rate(self):
        with self.assertRaises(TypeError):
            convert_minor_units(1000, "EUR", "USD", 1.08)

    def test_rejects_float_amount(self):
        with self.assertRaises(TypeError):
            convert_minor_units(10.0, "EUR", "USD", "1.08")

    def test_rejects_non_positive_rate(self):
        with self.assertRaises(ValueError):
            convert_minor_units(1000, "EUR", "USD", "0")
        with self.assertRaises(ValueError):
            convert_minor_units(1000, "EUR", "USD", "-1.08")

    def test_rejects_garbage_rate(self):
        with self.assertRaises(ValueError):
            convert_minor_units(1000, "EUR", "USD", "not a rate")

    def test_unknown_currency_raises(self):
        with self.assertRaises(KeyError):
            convert_minor_units(1000, "XXX", "USD", "1.08")

    def test_default_rounding_matches_explicit_half_up(self):
        self.assertEqual(
            convert_minor_units(333, "EUR", "USD", "1.005", rounding=ROUND_HALF_UP),
            convert_minor_units(333, "EUR", "USD", "1.005"),
        )


if __name__ == "__main__":
    unittest.main()
