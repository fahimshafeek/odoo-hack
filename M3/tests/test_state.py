"""
Tests for invoice state machine and D20 actions (INV-4, D20).
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest

from app.core_compat import AppError, today
from app.models import Discount, DiscountRedemption, Invoice
from app.state import (
    cancel_invoice,
    confirm_invoice,
)


def test_confirm_standard_invoice(db, admin_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-TEST01",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="draft",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("100.00"),
    )
    db.add(inv)
    db.commit()

    confirm_invoice(db, inv, admin_user)
    assert inv.status == "confirmed"
    assert inv.confirmed_at is not None


def test_d20_zero_total_invoice_confirms_straight_to_paid(db, admin_user):
    """
    D20 rule: if total = 0, confirm immediately transitions Draft -> Paid.
    """
    curr_date = today()
    inv = Invoice(
        number="INV-2026-ZERO",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="draft",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("0.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    confirm_invoice(db, inv, admin_user)
    assert inv.status == "paid"


def test_cancel_draft_releases_discount_usage(db, admin_user):
    """
    D20 rule: cancelling a Draft releases discount usage:
    deletes redemptions and decrements used_count.
    """
    curr_date = today()
    disc = Discount(
        name="Claimed Disc",
        type="percent",
        value=Decimal("10.00"),
        scope="subscription",
        usage_limit=5,
        used_count=1,
        start_date=curr_date - timedelta(days=5),
        end_date=curr_date + timedelta(days=5),
        is_active=True,
    )
    db.add(disc)
    db.flush()

    inv = Invoice(
        number="INV-2026-RELEASABLE",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="draft",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("90.00"),
    )
    db.add(inv)
    db.flush()

    red = DiscountRedemption(
        discount_id=disc.id, invoice_id=inv.id, amount=Decimal("10.00")
    )
    db.add(red)
    db.commit()

    # Cancel draft
    cancel_invoice(db, inv, admin_user)
    assert inv.status == "cancelled"

    # Verify used_count decremented
    reloaded_disc = db.get(Discount, disc.id)
    assert reloaded_disc.used_count == 0

    # Verify redemption deleted
    reloaded_red = db.get(DiscountRedemption, red.id)
    assert reloaded_red is None


def test_cancel_confirmed_with_payments_rejected(db, admin_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-PAIDPARTIAL",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("200.00"),
        amount_paid=Decimal("50.00"),
    )
    db.add(inv)
    db.commit()

    with pytest.raises(AppError) as exc:
        cancel_invoice(db, inv, admin_user)
    assert exc.value.status == 409
