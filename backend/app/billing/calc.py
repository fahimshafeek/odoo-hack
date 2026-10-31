"""
Pure invoice calculation maths (calc.py).
Zero database dependencies.
Enforces:
  - gross = q2(qty * unit_price)
  - net = gross - discount
  - tax = compute_tax(net, tax_rate)  (strictly computed AFTER discount, per line, half-up)
  - line_total = net + tax
  - Proportional allocation of subscription-scope discounts with rounding remainder absorbed by the last line.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.core.money import q2
from app.billing.tax import compute_tax


@dataclass
class LineInput:
    line_type: Literal["plan_fee", "product"]
    description: str
    product_id: uuid.UUID | None
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal
    position: int = 0


@dataclass
class ComputedLine:
    line_type: Literal["plan_fee", "product"]
    description: str
    product_id: uuid.UUID | None
    quantity: int
    unit_price: Decimal
    gross_amount: Decimal
    discount_id: uuid.UUID | None
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    position: int


@dataclass
class InvoiceTotals:
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    lines: list[ComputedLine] = field(default_factory=list)


def calculate_invoice_lines(
    lines: list[LineInput],
    line_discounts: dict[int, tuple[uuid.UUID | None, Decimal]] | None = None,
) -> InvoiceTotals:
    """
    Computes line amounts, tax after discount, and invoice totals.
    line_discounts maps line index to (discount_id, discount_amount).
    """
    discounts_map = line_discounts or {}
    computed_lines: list[ComputedLine] = []

    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    tax_total = Decimal("0.00")
    total = Decimal("0.00")

    for idx, item in enumerate(lines):
        gross = q2(Decimal(item.quantity) * item.unit_price)

        disc_id, disc_amt = discounts_map.get(idx, (None, Decimal("0.00")))
        # Clamped to line gross
        disc_amt = min(disc_amt, gross)
        disc_amt = q2(disc_amt)

        net = gross - disc_amt
        tax = compute_tax(net, item.tax_rate)
        line_tot = net + tax

        computed = ComputedLine(
            line_type=item.line_type,
            description=item.description,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            gross_amount=gross,
            discount_id=disc_id,
            discount_amount=disc_amt,
            tax_rate=item.tax_rate,
            tax_amount=tax,
            line_total=line_tot,
            position=item.position or idx,
        )
        computed_lines.append(computed)

        subtotal += gross
        discount_total += disc_amt
        tax_total += tax
        total += line_tot

    return InvoiceTotals(
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total=total,
        lines=computed_lines,
    )


def allocate_subscription_fixed_discount(
    lines: list[LineInput],
    discount_value: Decimal,
    eligible_indices: list[int],
) -> dict[int, Decimal]:
    """
    Allocates a subscription-scope fixed discount proportionally across eligible lines.
    The last line absorbs the rounding remainder so sum(allocations) == clamped discount_value.
    """
    if not eligible_indices or discount_value <= Decimal("0.00"):
        return {}

    eligible_gross_list = [
        q2(Decimal(lines[i].quantity) * lines[i].unit_price) for i in eligible_indices
    ]
    eligible_subtotal = sum(eligible_gross_list)

    if eligible_subtotal <= Decimal("0.00"):
        return {}

    actual_discount = min(discount_value, eligible_subtotal)
    allocations: dict[int, Decimal] = {}
    allocated_sum = Decimal("0.00")

    for i, idx in enumerate(eligible_indices):
        line_gross = eligible_gross_list[i]
        if i == len(eligible_indices) - 1:
            # Last line takes remainder
            line_disc = actual_discount - allocated_sum
        else:
            line_disc = q2(actual_discount * (line_gross / eligible_subtotal))
            allocated_sum += line_disc

        allocations[idx] = line_disc

    return allocations
