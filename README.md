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
