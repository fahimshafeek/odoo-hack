"""
Tests for payment recording and portal mock pay (PAY-1, PAY-2, D27).
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest

from app.core_compat import AppError, today
from app.models import Invoice
from app.payments import mock_pay, record_payment
from app.schemas import PaymentCreate
from app.state import derive_payment_state


def test_record_partial_then_full_payment(db, admin_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-PAYTEST",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    # 1. Partial payment: 400.00
    p1 = record_payment(
        db,
        inv.id,
        PaymentCreate(method="bank_transfer", amount=Decimal("400.00")),
        admin_user,
    )
    assert inv.amount_paid == Decimal("400.00")
    assert inv.status == "confirmed"
    assert derive_payment_state(inv, curr_date) == "partially_paid"

    # 2. Remaining balance payment: 600.00
    p2 = record_payment(
        db,
        inv.id,
        PaymentCreate(method="upi", amount=Decimal("600.00")),
        admin_user,
    )
    assert inv.amount_paid == Decimal("1000.00")
    assert inv.status == "paid"
    assert derive_payment_state(inv, curr_date) == "paid"


def test_overpayment_rejected(db, admin_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-OVERPAY",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("100.00"),
        amount_paid=Decimal("80.00"),
    )
    db.add(inv)
    db.commit()

    # Remaining balance is 20.00; paying 20.01 must fail with 422
    with pytest.raises(AppError) as exc:
        record_payment(
            db,
            inv.id,
            PaymentCreate(method="card", amount=Decimal("20.01")),
            admin_user,
        )
    assert exc.value.status == 422
    assert exc.value.code == "overpayment"


def test_payment_on_unconfirmed_rejected(db, admin_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-DRAFT",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="draft",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("100.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    with pytest.raises(AppError) as exc:
        record_payment(
            db,
            inv.id,
            PaymentCreate(method="cash", amount=Decimal("50.00")),
            admin_user,
        )
    assert exc.value.status == 409


def test_mock_pay_customer_portal(db, customer_user):
    curr_date = today()
    inv = Invoice(
        number="INV-2026-MOCKPAY",
        subscription_id=uuid.uuid4(),
        customer_id=customer_user.customer_id,
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    p = mock_pay(db, inv.id, customer_user)
    assert p.method == "online"
    assert p.amount == Decimal("500.00")
    assert inv.status == "paid"
