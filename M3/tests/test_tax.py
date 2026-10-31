"""
Tests for Tax computation in M3 (INV-2).
"""

from decimal import Decimal

import pytest

from app.tax import compute_tax


def test_tax_computation_standard():
    # 18% of 1560.00 = 280.80
    tax = compute_tax(Decimal("1560.00"), Decimal("18.00"))
    assert tax == Decimal("280.80")


def test_tax_computation_edges():
    # 12.5% of 100 = 12.50
    assert compute_tax(Decimal("100.00"), Decimal("12.50")) == Decimal("12.50")

    # Rate 0%
    assert compute_tax(Decimal("500.00"), Decimal("0.00")) == Decimal("0.00")

    # Rate 100%
    assert compute_tax(Decimal("250.50"), Decimal("100.00")) == Decimal("250.50")


def test_tax_half_up_rounding():
    # 0.005 half-up cases:
    # 10.05 * 5% = 0.5025 -> 0.50
    assert compute_tax(Decimal("10.05"), Decimal("5.00")) == Decimal("0.50")

    # 10.10 * 5% = 0.505 -> 0.51 (half-up)
    assert compute_tax(Decimal("10.10"), Decimal("5.00")) == Decimal("0.51")


def test_invalid_tax_rates():
    with pytest.raises(ValueError):
        compute_tax(Decimal("100.00"), Decimal("-1.00"))

    with pytest.raises(ValueError):
        compute_tax(Decimal("100.00"), Decimal("101.00"))
