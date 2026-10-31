"""
Discount engine and claim loop for M3 (DISC-1, DISC-2, DISC-3, D19).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.billing.calc import LineInput, allocate_subscription_fixed_discount
from app.core.money import q2
from app.billing.models import Discount


def get_editable_fields(discount: Discount) -> list[str]:
    """
    Returns list of field names that can be edited.
    Once used_count > 0, cannot change type, value, scope, or targets (D19).
    """
    base_fields = ["name", "end_date", "is_active", "usage_limit"]
    if discount.used_count == 0:
        return base_fields + [
            "type",
            "value",
            "scope",
            "min_purchase",
            "min_quantity",
            "start_date",
            "targets",
        ]
    return base_fields


def evaluate_discounts_for_lines(
    session: Session,
    lines: list[LineInput],
    subscription_id: uuid.UUID,
    as_of: date,
    excluded_discount_ids: set[uuid.UUID] | None = None,
) -> tuple[dict[int, tuple[uuid.UUID, Decimal]], set[uuid.UUID]]:
    """
    Evaluates active discounts against invoice candidate lines.
    Returns:
      (line_discounts_map: dict[line_index -> (discount_id, amount)],
       winning_discount_ids: set[discount_id])
    """
    excluded = excluded_discount_ids or set()

    # Query active discounts within date window
    stmt = select(Discount).where(
        Discount.is_active == True,
        Discount.start_date <= as_of,
        Discount.end_date >= as_of,
    )
    discounts = session.scalars(stmt).all()

    # Filter out excluded or exhausted
    active_candidates: list[Discount] = [
        d
        for d in discounts
        if d.id not in excluded
        and (d.usage_limit is None or d.used_count < d.usage_limit)
    ]

    if not active_candidates or not lines:
        return {}, set()

    # Map each candidate discount to candidate amounts per line
    discount_line_candidates: dict[uuid.UUID, dict[int, Decimal]] = {}

    for disc in active_candidates:
        target_product_ids = {
            t.product_id for t in disc.targets if t.product_id is not None
        }
        target_sub_ids = {
            t.subscription_id for t in disc.targets if t.subscription_id is not None
        }

        # Check subscription scope targeting
        if (
            disc.scope == "subscription"
            and target_sub_ids
            and subscription_id not in target_sub_ids
        ):
            continue

        # Find eligible lines
        eligible_indices: list[int] = []
        for idx, line in enumerate(lines):
            if disc.scope == "product":
                if line.line_type == "product":
                    if not target_product_ids or line.product_id in target_product_ids:
                        eligible_indices.append(idx)
            elif disc.scope == "subscription":
                # Subscription scope includes all lines (including plan fee)
                eligible_indices.append(idx)

        if not eligible_indices:
            continue

        # Subtotal & quantity checks
        eligible_subtotal = sum(
            q2(Decimal(lines[i].quantity) * lines[i].unit_price)
            for i in eligible_indices
        )
        eligible_quantity = sum(
            lines[i].quantity
            for i in eligible_indices
            if lines[i].line_type == "product"
        )

        if disc.min_purchase is not None and eligible_subtotal < disc.min_purchase:
            continue
        if disc.min_quantity is not None and eligible_quantity < disc.min_quantity:
            continue

        # Calculate candidate amounts per line
        candidate_amounts: dict[int, Decimal] = {}
        if disc.type == "percent":
            for idx in eligible_indices:
                line_gross = q2(Decimal(lines[idx].quantity) * lines[idx].unit_price)
                candidate_amounts[idx] = q2((line_gross * disc.value) / Decimal(100))
        elif disc.type == "fixed":
            if disc.scope == "product":
                # Fixed on product scope applies value per eligible line clamped to line gross
                for idx in eligible_indices:
                    line_gross = q2(
                        Decimal(lines[idx].quantity) * lines[idx].unit_price
                    )
                    candidate_amounts[idx] = min(disc.value, line_gross)
            elif disc.scope == "subscription":
                # Proportional allocation across eligible lines
                candidate_amounts = allocate_subscription_fixed_discount(
                    lines, disc.value, eligible_indices
                )

        discount_line_candidates[disc.id] = candidate_amounts

    # Best single discount per line
    line_discounts: dict[int, tuple[uuid.UUID, Decimal]] = {}
    winning_discounts: set[uuid.UUID] = set()

    for idx, line in enumerate(lines):
        best_disc_id: uuid.UUID | None = None
        best_amount = Decimal("0.00")

        for disc_id, amounts in discount_line_candidates.items():
            amt = amounts.get(idx, Decimal("0.00"))
            if amt > best_amount:
                best_amount = amt
                best_disc_id = disc_id

        if best_disc_id is not None and best_amount > Decimal("0.00"):
            line_discounts[idx] = (best_disc_id, best_amount)
            winning_discounts.add(best_disc_id)

    return line_discounts, winning_discounts


def claim_discount_usage_atomic(session: Session, discount_id: uuid.UUID) -> bool:
    """
    Atomically claims 1 usage of discount_id.
    Returns True if successfully claimed, False if exhausted.
    """
    discount = session.get(Discount, discount_id)
    if not discount or not discount.is_active:
        return False

    if discount.usage_limit is not None and discount.used_count >= discount.usage_limit:
        return False

    # Atomic update
    stmt = (
        update(Discount)
        .where(
            Discount.id == discount_id,
            (Discount.usage_limit.is_(None))
            | (Discount.used_count < Discount.usage_limit),
        )
        .values(used_count=Discount.used_count + 1)
    )
    result = session.execute(stmt)
    return result.rowcount > 0


def release_discount_usage(session: Session, discount_id: uuid.UUID) -> None:
    """
    Decrements used_count on discount when a Draft invoice is cancelled (D20).
    """
    session.execute(
        update(Discount)
        .where(Discount.id == discount_id, Discount.used_count > 0)
        .values(used_count=Discount.used_count - 1)
    )


def run_discount_claim_loop(
    session: Session,
    lines: list[LineInput],
    subscription_id: uuid.UUID,
    as_of: date,
    max_rounds: int = 5,
) -> tuple[dict[int, tuple[uuid.UUID, Decimal]], list[tuple[uuid.UUID, Decimal]]]:
    """
    Executes the 5-round claim loop (D19).
    Evaluates -> claims winning discounts -> if any claim fails, drops that discount and re-evaluates.
    Returns:
      (line_discounts_map, list of (discount_id, total_redemption_amount))
    """
    excluded_ids: set[uuid.UUID] = set()
    claimed_discounts: set[uuid.UUID] = set()

    for _ in range(max_rounds):
        line_discounts, winning_ids = evaluate_discounts_for_lines(
            session, lines, subscription_id, as_of, excluded_discount_ids=excluded_ids
        )

        if not winning_ids:
            return {}, []

        all_claimed = True
        for disc_id in winning_ids:
            if disc_id not in claimed_discounts:
                success = claim_discount_usage_atomic(session, disc_id)
                if success:
                    claimed_discounts.add(disc_id)
                else:
                    # Claim failed: exhausted by a concurrent process
                    excluded_ids.add(disc_id)
                    all_claimed = False

        if all_claimed:
            # Aggregate redemption totals per discount
            redemptions: dict[uuid.UUID, Decimal] = {}
            for disc_id, amt in line_discounts.values():
                redemptions[disc_id] = redemptions.get(disc_id, Decimal("0.00")) + amt

            redemption_list = [
                (disc_id, amt) for disc_id, amt in redemptions.items() if amt > 0
            ]
            return line_discounts, redemption_list

    # If exceeded max rounds, return without discounts
    return {}, []
