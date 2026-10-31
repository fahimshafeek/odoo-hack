"""
Tax computation utilities for M3 (INV-2).
"""

from __future__ import annotations

from decimal import Decimal

from app.core.money import tax_amount


def compute_tax(net: Decimal, rate_percent: Decimal) -> Decimal:
    """
    Computes tax on a net amount at rate_percent, quantized half-up to 2 decimal places.
    Tax is always computed on net (after discount), per line.
    """
    if rate_percent < Decimal("0.00") or rate_percent > Decimal("100.00"):
        raise ValueError("Tax rate must be between 0.00 and 100.00")
    if net < Decimal("0.00"):
        raise ValueError("Net amount cannot be negative")
    if rate_percent == Decimal("0.00") or net == Decimal("0.00"):
        return Decimal("0.00")

    return tax_amount(net, rate_percent)
