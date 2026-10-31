"""
Tests for discount engine and edit-locks (DISC-1, DISC-2, DISC-3, D19).
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest

from app.calc import LineInput
from app.core_compat import AppError, today
from app.discounts import (
    claim_discount_usage_atomic,
    evaluate_discounts_for_lines,
)
from app.models import Discount, DiscountTarget
from app.schemas import DiscountCreate, DiscountUpdate
from app.service import create_discount, update_discount


def test_discount_eligibility_and_best_selection(db):
    curr_date = today()
    sub_id = uuid.uuid4()
    prod_a = uuid.uuid4()
    prod_b = uuid.uuid4()

    # Discount 1: 10% on Product A
    d1 = Discount(
        name="10% on Prod A",
        type="percent",
        value=Decimal("10.00"),
        scope="product",
        start_date=curr_date - timedelta(days=5),
        end_date=curr_date + timedelta(days=5),
        is_active=True,
    )
    db.add(d1)
    db.flush()
    db.add(DiscountTarget(discount_id=d1.id, product_id=prod_a))

    # Discount 2: 20% on Product A
    d2 = Discount(
        name="20% on Prod A",
        type="percent",
        value=Decimal("20.00"),
        scope="product",
        start_date=curr_date - timedelta(days=5),
        end_date=curr_date + timedelta(days=5),
        is_active=True,
    )
    db.add(d2)
    db.flush()
    db.add(DiscountTarget(discount_id=d2.id, product_id=prod_a))
    db.commit()

    lines = [
        LineInput(
            line_type="product",
            description="Item A",
            product_id=prod_a,
            quantity=1,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.00"),
        ),
        LineInput(
            line_type="product",
            description="Item B",
            product_id=prod_b,
            quantity=1,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.00"),
        ),
    ]

    line_discs, winners = evaluate_discounts_for_lines(db, lines, sub_id, curr_date)

    # Line 0 should pick the best: 20% (d2) -> 20.00
    assert 0 in line_discs
    assert line_discs[0][0] == d2.id
    assert line_discs[0][1] == Decimal("20.00")

    # Line 1 (Product B) gets no discount
    assert 1 not in line_discs
    assert winners == {d2.id}


def test_discount_min_purchase_and_quantity_edges(db):
    curr_date = today()
    sub_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    disc = Discount(
        name="Bulk discount",
        type="fixed",
        value=Decimal("50.00"),
        scope="product",
        min_purchase=Decimal("200.00"),
        min_quantity=2,
        start_date=curr_date - timedelta(days=5),
        end_date=curr_date + timedelta(days=5),
        is_active=True,
    )
    db.add(disc)
    db.commit()

    # Subtotal 150 < 200 -> Ineligible
    lines_fail = [
        LineInput(
            line_type="product",
            description="Item",
            product_id=prod_id,
            quantity=1,
            unit_price=Decimal("150.00"),
            tax_rate=Decimal("0.00"),
        )
    ]
    discs, _ = evaluate_discounts_for_lines(db, lines_fail, sub_id, curr_date)
    assert not discs

    # Subtotal exactly 200 and qty exactly 2 -> Eligible!
    lines_pass = [
        LineInput(
            line_type="product",
            description="Item",
            product_id=prod_id,
            quantity=2,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.00"),
        )
    ]
    discs, _ = evaluate_discounts_for_lines(db, lines_pass, sub_id, curr_date)
    assert 0 in discs
    assert discs[0][1] == Decimal("50.00")


def test_discount_usage_limit_atomic_claim(db):
    curr_date = today()
    disc = Discount(
        name="Limited 2",
        type="percent",
        value=Decimal("10.00"),
        scope="subscription",
        usage_limit=2,
        used_count=0,
        start_date=curr_date - timedelta(days=5),
        end_date=curr_date + timedelta(days=5),
        is_active=True,
    )
    db.add(disc)
    db.commit()

    # Claim 1 -> success
    assert claim_discount_usage_atomic(db, disc.id) is True
    db.commit()

    # Claim 2 -> success
    assert claim_discount_usage_atomic(db, disc.id) is True
    db.commit()

    # Claim 3 -> fails (exhausted)
    assert claim_discount_usage_atomic(db, disc.id) is False
    db.commit()

    reloaded = db.get(Discount, disc.id)
    assert reloaded.used_count == 2


def test_d19_edit_lock_when_used(db):
    curr_date = today()
    data = DiscountCreate(
        name="Discount Alpha",
        type="percent",
        value=Decimal("15.00"),
        scope="subscription",
        start_date=curr_date,
        end_date=curr_date + timedelta(days=30),
        usage_limit=5,
    )
    out = create_discount(db, data)
    db.commit()

    disc = db.get(Discount, out.id)
    # Simulate a usage
    disc.used_count = 1
    db.commit()

    # Attempting to change value -> 409 conflict
    with pytest.raises(AppError) as exc:
        update_discount(db, disc.id, DiscountUpdate(value=Decimal("20.00")))
    assert exc.value.status == 409

    # Attempting to change type -> 409 conflict
    with pytest.raises(AppError) as exc:
        update_discount(db, disc.id, DiscountUpdate(type="fixed"))
    assert exc.value.status == 409

    # Changing name or extending end_date is ALLOWED
    updated = update_discount(
        db,
        disc.id,
        DiscountUpdate(
            name="Discount Alpha Renamed", end_date=curr_date + timedelta(days=60)
        ),
    )
    assert updated.name == "Discount Alpha Renamed"
