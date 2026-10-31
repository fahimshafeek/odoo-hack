"""
Tests for invoice line calculation and maths (calc.py, plan 9.2, D19).
"""

import uuid
from decimal import Decimal

from app.calc import (
    LineInput,
    allocate_subscription_fixed_discount,
    calculate_invoice_lines,
)


def test_hand_computed_fixture_from_prompt():
    """
    Prompt requirement:
    Odoo line 1,000 + 560 = 1,560 x qty 5 with a 10% discount and 18% tax =
    gross 7,800.00, discount 780.00, net 7,020.00, tax 1,263.60, total 8,283.60
    """
    disc_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    lines = [
        LineInput(
            line_type="product",
            description="Odoo Variant License",
            product_id=prod_id,
            quantity=5,
            unit_price=Decimal("1560.00"),
            tax_rate=Decimal("18.00"),
        )
    ]

    # Line 0 gets 10% discount: 7800 * 10% = 780.00
    discounts_map = {0: (disc_id, Decimal("780.00"))}

    totals = calculate_invoice_lines(lines, discounts_map)

    assert totals.subtotal == Decimal("7800.00")
    assert totals.discount_total == Decimal("780.00")
    assert totals.tax_total == Decimal("1263.60")
    assert totals.total == Decimal("8283.60")

    line0 = totals.lines[0]
    assert line0.gross_amount == Decimal("7800.00")
    assert line0.discount_amount == Decimal("780.00")
    assert line0.tax_amount == Decimal("1263.60")
    assert line0.line_total == Decimal("8283.60")


def test_tax_computed_strictly_after_discount():
    """
    Verifies that tax is calculated on net (gross - discount), NOT gross.
    """
    lines = [
        LineInput(
            line_type="product",
            description="Service Item",
            product_id=uuid.uuid4(),
            quantity=1,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("10.00"),
        )
    ]
    # Discount 50.00 -> net 50.00 -> tax 10% = 5.00, line_total = 55.00
    discounts_map = {0: (uuid.uuid4(), Decimal("50.00"))}
    totals = calculate_invoice_lines(lines, discounts_map)

    assert totals.subtotal == Decimal("100.00")
    assert totals.discount_total == Decimal("50.00")
    assert totals.tax_total == Decimal("5.00")
    assert totals.total == Decimal("55.00")


def test_proportional_subscription_discount_allocation():
    """
    Tests proportional allocation across lines with rounding remainder absorbed by the last line.
    """
    lines = [
        LineInput(
            line_type="product",
            description="Item 1",
            product_id=uuid.uuid4(),
            quantity=1,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.00"),
        ),
        LineInput(
            line_type="product",
            description="Item 2",
            product_id=uuid.uuid4(),
            quantity=1,
            unit_price=Decimal("200.00"),
            tax_rate=Decimal("0.00"),
        ),
        LineInput(
            line_type="product",
            description="Item 3",
            product_id=uuid.uuid4(),
            quantity=1,
            unit_price=Decimal("300.00"),
            tax_rate=Decimal("0.00"),
        ),
    ]
    # Total gross = 600.00. Discount = 100.00.
    # Line 0 (1/6): 16.67
    # Line 1 (2/6): 33.33
    # Line 2 (3/6): 100.00 - (16.67 + 33.33) = 50.00 (absorbs remainder)
    allocations = allocate_subscription_fixed_discount(
        lines, Decimal("100.00"), [0, 1, 2]
    )

    assert allocations[0] == Decimal("16.67")
    assert allocations[1] == Decimal("33.33")
    assert allocations[2] == Decimal("50.00")
    assert sum(allocations.values()) == Decimal("100.00")
