from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any
from pydantic import BeforeValidator, PlainSerializer


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


def q2(x: Decimal) -> Decimal:
    """Quantize to 2 decimal places using standard ROUND_HALF_UP."""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def tax_amount(net: Decimal, rate_percent: Decimal) -> Decimal:
    """Calculate tax amount rounded half-up: q2(net * rate / 100)."""
    return q2(net * rate_percent / Decimal("100"))


def _validate_money(v: Any) -> Decimal:
    d = to_decimal(v)
    if d < 0:
        raise ValueError("Money value cannot be negative")
    # Check max 2 decimal places
    tuple_val = d.as_tuple()
    if tuple_val.exponent < -2:
        raise ValueError("Money value cannot have more than 2 decimal places")
    return q2(d)


def _serialize_money(v: Decimal) -> str:
    return f"{q2(v):.2f}"


Money = Annotated[
    Decimal,
    BeforeValidator(_validate_money),
    PlainSerializer(_serialize_money, return_type=str, when_used="json"),
]
