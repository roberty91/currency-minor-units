"""Convert currency amounts between minor-unit integers and decimal strings.

Payment APIs and ledgers store amounts as integers in the currency's
smallest unit (e.g. 1050 = $10.50) to avoid floating point rounding.
Reports and user-facing text want a decimal string instead. Converting
between the two requires knowing how many decimal places a currency
uses, which is not the same for every currency (JPY has none, BHD has
three, most others have two).
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# ISO 4217 minor unit counts, grouped by exponent rather than alphabetically
# so it's obvious at a glance which bucket a given currency falls into.
#
# MGA (Malagasy ariary) and MRU (Mauritanian ouguiya) are officially
# subdivided into fifths rather than tenths, but ISO 4217 still lists them
# with 2 decimal digits, so they're grouped here with the rest of the
# 2-decimal currencies rather than treated as a special case.
_ZERO_DECIMAL = (
    "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "PYG", "RWF",
    "UGX", "UYI", "VND", "VUV", "XAF", "XOF", "XPF",
)

_TWO_DECIMAL = (
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BMD", "BND", "BOB", "BRL", "BSD", "BTN",
    "BWP", "BYN", "BZD", "CAD", "CDF", "CHF", "COP", "CRC", "CUC", "CUP",
    "CVE", "CZK", "DKK", "DOP", "DZD", "EGP", "ERN", "ETB", "EUR", "FJD",
    "FKP", "GBP", "GEL", "GHS", "GIP", "GMD", "GTQ", "GYD", "HKD", "HNL",
    "HTG", "HUF", "IDR", "ILS", "INR", "JMD", "KES", "KGS", "KHR", "KYD",
    "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "MAD", "MDL", "MGA", "MKD",
    "MMK", "MNT", "MOP", "MRU", "MUR", "MVR", "MWK", "MXN", "MYR", "MZN",
    "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "PAB", "PEN", "PGK", "PHP",
    "PKR", "PLN", "QAR", "RON", "RSD", "RUB", "SAR", "SBD", "SCR", "SDG",
    "SEK", "SGD", "SHP", "SLE", "SOS", "SRD", "SSP", "STN", "SVC", "SYP",
    "SZL", "THB", "TJS", "TMT", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH",
    "USD", "UYU", "UZS", "VES", "WST", "XCD", "YER", "ZAR", "ZMW",
)

_THREE_DECIMAL = ("BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND")

# Non-circulating settlement currencies that use a fourth decimal place.
_FOUR_DECIMAL = ("CLF", "UYW")

_EXPONENTS = {
    **{code: 0 for code in _ZERO_DECIMAL},
    **{code: 2 for code in _TWO_DECIMAL},
    **{code: 3 for code in _THREE_DECIMAL},
    **{code: 4 for code in _FOUR_DECIMAL},
}

# Single-character symbols only. Multi-character ones like "kr" or "zł"
# are left alone because they overlap with letters that show up in real
# amounts (e.g. a stray "kr" could just as easily be someone's initials
# in a pasted spreadsheet cell), so stripping them risks corrupting the
# number instead of cleaning it up.
_CURRENCY_SYMBOLS = frozenset("$€£¥₹₩₽₺₴₪₫₦₱฿₡₲₵₸₭₮")


def exponent_for(currency: str) -> int:
    """Return how many decimal places minor units use for a currency.

    Raises KeyError for unknown codes instead of guessing, because a wrong
    guess (e.g. treating JPY like USD) is a silent 100x error, not a crash
    someone would notice.
    """
    code = currency.upper()
    if code not in _EXPONENTS:
        raise KeyError(f"unknown currency code: {currency!r}")
    return _EXPONENTS[code]


def minor_units_to_decimal(amount: int, currency: str) -> Decimal:
    """Turn an integer minor-unit amount into an exact Decimal."""
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("minor units must be an int")
    exponent = exponent_for(currency)
    return Decimal(amount).scaleb(-exponent)


def minor_units_to_string(amount: int, currency: str) -> str:
    """Turn an integer minor-unit amount into a plain decimal string.

    e.g. minor_units_to_string(1050, "USD") -> "10.50"
         minor_units_to_string(500, "JPY") -> "500"
    """
    exponent = exponent_for(currency)
    value = minor_units_to_decimal(amount, currency)
    quantized = value.quantize(Decimal(1).scaleb(-exponent))
    return str(quantized)


def decimal_to_minor_units(value, currency: str) -> int:
    """Turn a decimal string (or Decimal) into an integer minor-unit amount.

    Rejects floats outright: a float can't represent 10.50 exactly, so
    accepting one would just move the rounding bug one call earlier.
    Also rejects strings with more precision than the currency allows
    (e.g. "10.505" for USD) rather than silently truncating them.
    """
    if isinstance(value, float):
        raise TypeError(
            "pass a str or Decimal, not float — floats can't represent "
            "exact currency amounts"
        )

    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"not a valid decimal amount: {value!r}") from exc

    exponent = exponent_for(currency)
    scaled = decimal_value.scaleb(exponent)

    if scaled != scaled.to_integral_value():
        places = "place" if exponent == 1 else "places"
        raise ValueError(
            f"{value!r} has more precision than {currency.upper()} allows "
            f"({exponent} decimal {places})"
        )
    return int(scaled)


def convert_minor_units(
    amount: int,
    from_currency: str,
    to_currency: str,
    rate,
    rounding=ROUND_HALF_UP,
) -> int:
    """Convert a minor-unit amount from one currency to another via an exchange rate.

    `rate` is the price of one unit of `from_currency` in `to_currency`
    (e.g. rate="1.08" converting EUR to USD means 1 EUR buys 1.08 USD).
    Pass a str or Decimal, not a float, for the same exactness reasons as
    `decimal_to_minor_units`.

    Unlike `decimal_to_minor_units`, this rounds instead of rejecting
    extra precision: an exchange rate almost never lands exactly on a
    whole minor unit of the target currency, so something has to give,
    and `rounding` (a `decimal` module rounding mode) controls how.
    """
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("minor units must be an int")
    if isinstance(rate, float):
        raise TypeError(
            "pass a str or Decimal for rate, not float — floats can't "
            "represent exact exchange rates"
        )

    try:
        rate_value = Decimal(rate)
    except InvalidOperation as exc:
        raise ValueError(f"not a valid exchange rate: {rate!r}") from exc

    if rate_value <= 0:
        raise ValueError(f"exchange rate must be positive, got {rate!r}")

    source_amount = minor_units_to_decimal(amount, from_currency)
    target_exponent = exponent_for(to_currency)
    target_amount = source_amount * rate_value
    quantized = target_amount.quantize(
        Decimal(1).scaleb(-target_exponent), rounding=rounding
    )
    return int(quantized)


def _split_thousands_separator(text: str) -> str:
    """Rewrite a string with at most one kind of separator into plain decimal form.

    Whichever of ',' or '.' shows up gets treated as a thousands separator
    when it's followed by exactly three digits (the standard grouping
    width) and as a decimal point otherwise.
    """
    for sep in (",", "."):
        count = text.count(sep)
        if count == 0:
            continue
        digits_after_last = len(text) - text.rfind(sep) - 1
        if count > 1 or digits_after_last == 3:
            return text.replace(sep, "")
        return text.replace(sep, ".") if sep != "." else text
    return text


def _normalize_formatted_number(text: str) -> str:
    """Turn a formatted number like "1.050,00" or "1,050" into plain decimal text."""
    has_comma = "," in text
    has_period = "." in text
    if has_comma and has_period:
        last_comma = text.rfind(",")
        last_period = text.rfind(".")
        if last_comma > last_period:
            decimal_sep, thousands_sep = ",", "."
        else:
            decimal_sep, thousands_sep = ".", ","
        cleaned = text.replace(thousands_sep, "")
        if decimal_sep != ".":
            cleaned = cleaned.replace(decimal_sep, ".")
        return cleaned
    return _split_thousands_separator(text)


def formatted_string_to_minor_units(text: str, currency: str) -> int:
    """Parse a human-formatted amount into an integer minor-unit amount.

    Handles the things a plain `decimal_to_minor_units` call rejects:
    thousands separators, a small set of single-character currency
    symbols, the currency's own ISO code as a prefix or suffix, and
    parentheses or a leading minus sign for negative amounts.

    e.g. formatted_string_to_minor_units("$1,050.00", "USD") -> 105000
         formatted_string_to_minor_units("1.050,00", "EUR") -> 105000
         formatted_string_to_minor_units("(10.50)", "USD") -> -1050
         formatted_string_to_minor_units("JPY 1,050", "JPY") -> 1050

    Whether a lone comma or period is a thousands separator or a decimal
    point is inferred from context (three digits after it means
    thousands separator, anything else means decimal point), not from a
    fixed locale, so genuinely ambiguous input like "10,000" for a
    three-decimal currency can still be misread. When in doubt, pass an
    unambiguous string with both a thousands separator and a decimal
    point, or use `decimal_to_minor_units` directly.
    """
    if not isinstance(text, str):
        raise TypeError("amount must be a str")

    stripped = text.strip()
    if not stripped:
        raise ValueError("empty amount string")

    negative = False
    if stripped.startswith("(") and stripped.endswith(")"):
        negative = True
        stripped = stripped[1:-1].strip()

    if stripped.startswith("-"):
        negative = True
        stripped = stripped[1:].strip()
    elif stripped.startswith("+"):
        stripped = stripped[1:].strip()

    code = currency.upper()
    upper = stripped.upper()
    if upper.startswith(code):
        stripped = stripped[len(code):].strip()
    elif upper.endswith(code):
        stripped = stripped[: len(stripped) - len(code)].strip()

    if stripped and stripped[0] in _CURRENCY_SYMBOLS:
        stripped = stripped[1:].strip()
    elif stripped and stripped[-1] in _CURRENCY_SYMBOLS:
        stripped = stripped[:-1].strip()

    if stripped.startswith("-"):
        negative = True
        stripped = stripped[1:].strip()
    elif stripped.startswith("+"):
        stripped = stripped[1:].strip()

    if not stripped:
        raise ValueError(f"not a valid amount: {text!r}")

    normalized = _normalize_formatted_number(stripped)
    if negative:
        normalized = "-" + normalized

    return decimal_to_minor_units(normalized, currency)
