"""
Tests for billing engine orchestrator (INV-1, INV-5, plan 9.3).
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from app.core_compat import today
from app.engine import run_billing
from app.models import Invoice, SubscriptionLineStub, SubscriptionStub


def test_billing_engine_run_and_idempotency(db_session_factory, admin_user):
    """
    Verifies that running billing engine twice creates invoices on first run,
    and exactly 0 duplicates on the second run.
    """
    curr_date = today()
    sub_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    session = db_session_factory()
    sub = SubscriptionStub(
        id=sub_id,
        number="SUB-2026-ENG01",
        customer_id=cust_id,
        status="active",
        billing_period="monthly",
        start_date=curr_date,
        expiry_date=curr_date + timedelta(days=90),
        next_billing_date=curr_date,
        plan_price=Decimal("200.00"),
        plan_tax_rate=Decimal("18.00"),
        due_days=15,
        lines=[
            SubscriptionLineStub(
                product_id=prod_id,
                description="Service Plan Pro",
                quantity=1,
                unit_price=Decimal("800.00"),
                tax_rate=Decimal("18.00"),
                position=1,
            )
        ],
    )
    session.add(sub)
    session.commit()
    session.close()

    # Run 1: Should create 1 invoice
    run_billing(db_session_factory, as_of=curr_date, triggered_by=admin_user.id)

    session2 = db_session_factory()
    invs = session2.query(Invoice).filter_by(subscription_id=sub_id).all()
    assert len(invs) == 1
    inv0 = invs[0]
    assert inv0.subtotal == Decimal("1000.00")  # 200 plan fee + 800 line
    assert inv0.tax_total == Decimal("180.00")  # 18% of 1000
    assert inv0.total == Decimal("1180.00")
    session2.close()

    # Run 2: Immediately run again for same date -> ZERO duplicates
    run_billing(db_session_factory, as_of=curr_date, triggered_by=admin_user.id)

    session3 = db_session_factory()
    invs_after = session3.query(Invoice).filter_by(subscription_id=sub_id).all()
    assert len(invs_after) == 1  # Still exactly 1!
    session3.close()


def test_billing_engine_catch_up_three_days(db_session_factory, admin_user):
    """
    If worker was down for 3 days on a daily plan, engine creates 3 catch-up invoices.
    """
    curr_date = today()
    sub_id = uuid.uuid4()
    session = db_session_factory()

    # Daily plan started 2 days ago, next_billing_date was 2 days ago
    start = curr_date - timedelta(days=2)
    sub = SubscriptionStub(
        id=sub_id,
        number="SUB-2026-DAILY",
        customer_id=uuid.uuid4(),
        status="active",
        billing_period="daily",
        start_date=start,
        expiry_date=curr_date + timedelta(days=30),
        next_billing_date=start,
        plan_price=Decimal("10.00"),
        plan_tax_rate=Decimal("0.00"),
        due_days=5,
        lines=[],
    )
    session.add(sub)
    session.commit()
    session.close()

    # Run billing as of today -> should catch up 3 daily periods:
    # Day -2, Day -1, Day 0
    run_billing(db_session_factory, as_of=curr_date, triggered_by=admin_user.id)

    session2 = db_session_factory()
    invs = (
        session2.query(Invoice)
        .filter_by(subscription_id=sub_id)
        .order_by(Invoice.period_start)
        .all()
    )
    assert len(invs) == 3

    assert invs[0].period_start == start
    assert invs[1].period_start == start + timedelta(days=1)
    assert invs[2].period_start == curr_date
    session2.close()


def test_paused_closed_subscriptions_never_invoiced(db_session_factory, admin_user):
    curr_date = today()
    session = db_session_factory()

    sub_paused = SubscriptionStub(
        number="SUB-PAUSED",
        customer_id=uuid.uuid4(),
        status="paused",
        billing_period="monthly",
        start_date=curr_date,
        expiry_date=curr_date + timedelta(days=60),
        next_billing_date=curr_date,
    )
    sub_closed = SubscriptionStub(
        number="SUB-CLOSED",
        customer_id=uuid.uuid4(),
        status="closed",
        billing_period="monthly",
        start_date=curr_date,
        expiry_date=curr_date + timedelta(days=60),
        next_billing_date=curr_date,
    )
    session.add_all([sub_paused, sub_closed])
    session.commit()
    paused_id = sub_paused.id
    closed_id = sub_closed.id
    session.close()

    run_billing(db_session_factory, as_of=curr_date, triggered_by=admin_user.id)

    session2 = db_session_factory()
    assert session2.query(Invoice).filter_by(subscription_id=paused_id).count() == 0
    assert session2.query(Invoice).filter_by(subscription_id=closed_id).count() == 0
    session2.close()
