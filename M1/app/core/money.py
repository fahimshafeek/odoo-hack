from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any
from pydantic import BeforeValidator

TWO_PLACES = Decimal("0.01")

def to_decimal(val: Any) -> Decimal:
    """Converts strings, ints, or Decimals to Decimal. Rejects raw floats to prevent precision bugs."""
    if isinstance(val, float):
        raise ValueError("Float values are strictly forbidden in monetary math. Use string or Decimal.")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))

def q2(value: Decimal) -> Decimal:
    """Rounds to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def tax_amount(net_amount: Decimal, rate_percent: Decimal) -> Decimal:
    """Computes line tax amount after discount: round_half_up(net * rate / 100)."""
    return q2(net_amount * (rate_percent / Decimal("100")))

def format_money(val: Decimal | str | None) -> str:
    """Formats Decimal as string with exactly two decimal places."""
    if val is None:
        return "0.00"
    dec = to_decimal(val)
    return f"{q2(dec):.2f}"

# Pydantic type annotation that parses input to Decimal and outputs string "1560.00"
Money = Annotated[Decimal, BeforeValidator(to_decimal)]
