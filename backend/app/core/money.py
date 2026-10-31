from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any
from pydantic import BeforeValidator, PlainSerializer

TWO_PLACES = Decimal("0.01")


def to_decimal(v: Any) -> Decimal:
    """Convert input to Decimal. Explicitly rejects floats to prevent precision bugs."""
    if isinstance(v, float):
        raise ValueError("Float values are strictly forbidden for money computation; use str, int or Decimal")
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, str)):
        try:
            return Decimal(str(v).strip())
        except Exception as e:
            raise ValueError(f"Invalid decimal string: {v}") from e
    raise ValueError(f"Cannot convert type {type(v).__name__} to Decimal")


def q2(value: Any) -> Decimal:
    """Quantize to 2 decimal places using ROUND_HALF_UP."""
    dec = to_decimal(value)
    return dec.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def format_money(value: Any, symbol: str = "") -> str:
    """Formats Decimal value with 2 decimal places (plain decimal by default, with symbol if specified)."""
    if value is None:
        return "0.00"
    dec = q2(value)
    if symbol:
        return f"{symbol}{dec:,.2f}"
    return f"{dec:.2f}"


def tax_amount(net: Decimal, rate_percent: Decimal) -> Decimal:
    """Compute tax on net amount at rate_percent, quantized half-up."""
    return q2((net * rate_percent) / Decimal(100))


def _validate_money(v: Any) -> Decimal:
    d = to_decimal(v)
    if d < 0:
        raise ValueError("Money value cannot be negative")
    tuple_val = d.as_tuple()
    if tuple_val.exponent < -2:
        raise ValueError("Money value cannot have more than 2 decimal places")
    return q2(d)


def _serialize_money(v: Decimal) -> str:
    return f"{v:.2f}"


Money = Annotated[
    Decimal,
    BeforeValidator(_validate_money),
    PlainSerializer(_serialize_money, return_type=str),
]
