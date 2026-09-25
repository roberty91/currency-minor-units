# currency-minor-units

Convert currency amounts between two formats:

- **minor units** — an integer in the currency's smallest unit, e.g. `1050`
  for ten dollars fifty cents. This is what payment processors, ledgers,
  and most money-handling APIs use, because integers don't have floating
  point rounding problems.
- **decimal string** — a human-readable amount, e.g. `"10.50"`. This is
  what shows up in invoices, reports, and CSV exports.

The tricky part is that "smallest unit" isn't two decimal places for
every currency. Japanese yen has none. Bahraini dinar has three. Getting
this wrong doesn't crash — it silently produces an amount that's off by
a factor of 10, 100, or 1000, which is worse than a crash.

## Usage

```python
from currency_minor_units import minor_units_to_string, decimal_to_minor_units

minor_units_to_string(1050, "USD")   # "10.50"
minor_units_to_string(500, "JPY")    # "500"
minor_units_to_string(1500, "BHD")   # "1.500"

decimal_to_minor_units("10.50", "USD")  # 1050
decimal_to_minor_units("500", "JPY")    # 500

# more decimal places than the currency allows is an error, not a
# silent truncation
decimal_to_minor_units("10.505", "USD")  # raises ValueError
```

There's also `exponent_for(currency)` if you just need to know how many
decimal places a currency uses, and `minor_units_to_decimal(amount,
currency)` if you want a `decimal.Decimal` instead of a formatted string
(e.g. to do further arithmetic before displaying it).

For amounts that come from user input, spreadsheets, or invoices rather
than an API, `formatted_string_to_minor_units` handles the things
`decimal_to_minor_units` deliberately rejects: thousands separators, a
currency symbol, the currency's own ISO code as a prefix or suffix, and
parentheses or a leading minus sign for negative amounts.

```python
from currency_minor_units import formatted_string_to_minor_units

formatted_string_to_minor_units("$1,050.00", "USD")  # 105000
formatted_string_to_minor_units("1.050,00", "EUR")   # 105000
formatted_string_to_minor_units("(10.50)", "USD")    # -1050
formatted_string_to_minor_units("JPY 1,050", "JPY")  # 1050
```

Whether a lone comma or period is a thousands separator or a decimal
point is inferred from context (three digits after it means thousands
separator, anything else means decimal point), not from a fixed locale,
so genuinely ambiguous input like `"10,000"` for a three-decimal
currency can still be misread. When in doubt, pass an unambiguous
string with both a thousands separator and a decimal point, or use
`decimal_to_minor_units` directly.

For converting an amount from one currency to another at an exchange
rate, use `convert_minor_units`. Unlike `decimal_to_minor_units`, it
rounds rather than rejecting extra precision, because an exchange rate
multiplication almost never lands exactly on a whole minor unit of the
target currency:

```python
from currency_minor_units import convert_minor_units

# 10.00 EUR at a rate of 1 EUR = 1.08 USD
convert_minor_units(1000, "EUR", "USD", "1.08")  # 1080

# rounding mode defaults to ROUND_HALF_UP; pass any decimal.ROUND_*
# constant to change it
from decimal import ROUND_DOWN
convert_minor_units(333, "EUR", "USD", "1.005", rounding=ROUND_DOWN)  # 334
```

`rate` is the price of one unit of the source currency in the target
currency, and must be a `str` or `Decimal` for the same reason floats
are rejected elsewhere in this library: `1.08` can't always be
represented exactly as a float.

Every public function is pure — same input, same output, no I/O, no
shared state — which is what makes them straightforward to unit test
and safe to use inside larger pipelines.

Floats are rejected on the way in (`decimal_to_minor_units(10.5, ...)`
raises `TypeError`) because `10.5` can't always be represented exactly
as a float, and money should never take that risk. Pass a string or a
`Decimal` instead.

Currency coverage follows the ISO 4217 exponent table (see `_EXPONENTS`
in `src/currency_minor_units/converter.py`) rather than a payment
processor's "zero-decimal currency" list, so a couple of codes are
worth calling out: MGA and MRU are subdivided into fifths rather than
tenths, but ISO 4217 still assigns them 2 decimal digits, and CLF/UYW
are non-circulating settlement currencies with 4 decimal digits. Codes
that aren't in the table raise `KeyError` rather than guessing.

## Installing

No PyPI package yet. Clone the repo and install it locally:

```
pip install -e .
```

It has no dependencies beyond the Python standard library.

## Running the tests

```
python -m unittest discover tests
```
