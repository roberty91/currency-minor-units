"""Convert currency amounts between minor-unit integers and decimal strings.

Payment APIs and ledgers store amounts as integers in the currency's
smallest unit (e.g. 1050 = $10.50) to avoid floating point rounding.
Reports and user-facing text want a decimal string instead. Converting
between the two requires knowing how many decimal places a currency
uses, which is not the same for every currency (JPY has none, BHD has
three, most others have two).
"""

from decimal import Decimal, InvalidOperation

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
