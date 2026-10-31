import datetime
from decimal import Decimal
import pytest
from app.subscriptions.jobs import (
    activate_due,
    expire_quotes,
    auto_close_expired,
    flag_upcoming_renewals,
)
from app.subscriptions.models import Subscription
from tests.factories import (
    create_test_tax,
    create_test_product,
    create_test_plan,
    create_test_payment_term,
    create_test_customer,
    create_test_subscription,
)


def test_activate_due_job(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Confirmed sub with start_date = 2026-06-01
    sub1 = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="confirmed",
        start_date=datetime.date(2026, 6, 1),
        expiry_date=datetime.date(2027, 6, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    # Sub with future start date = 2026-07-01
    sub2 = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="confirmed",
        start_date=datetime.date(2026, 7, 1),
        expiry_date=datetime.date(2027, 7, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    # Run as of 2026-06-15
    count = activate_due(db, as_of=datetime.date(2026, 6, 15))
    assert count == 1
    assert sub1.status == "active"
    assert sub1.next_billing_date == sub1.start_date
    assert sub2.status == "confirmed"


def test_expire_quotes_job(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Quotation valid until 2026-05-10
    sub_expired = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="quotation",
        start_date=datetime.date(2026, 5, 1),
        expiry_date=datetime.date(2027, 5, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    sub_expired.quote_valid_until = datetime.date(2026, 5, 10)

    # Quotation valid until 2026-05-25
    sub_valid = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="quotation",
        start_date=datetime.date(2026, 5, 1),
        expiry_date=datetime.date(2027, 5, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    sub_valid.quote_valid_until = datetime.date(2026, 5, 25)

    # Run job as of 2026-05-15
    count = expire_quotes(db, as_of=datetime.date(2026, 5, 15))
    assert count == 1
    assert sub_expired.status == "closed"
    assert sub_valid.status == "quotation"


def test_auto_close_expired_job(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan_auto = create_test_plan(db, auto_close=True)
    plan_manual = create_test_plan(db, auto_close=False)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Sub with auto_close=True, expired on 2026-05-01
    sub_auto = create_test_subscription(
        db,
        cust,
        plan_auto,
        term,
        status="active",
        start_date=datetime.date(2025, 5, 1),
        expiry_date=datetime.date(2026, 5, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    # Sub with auto_close=False, expired on 2026-05-01
    sub_manual = create_test_subscription(
        db,
        cust,
        plan_manual,
        term,
        status="active",
        start_date=datetime.date(2025, 5, 1),
        expiry_date=datetime.date(2026, 5, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    # Run job as of 2026-05-10
    count = auto_close_expired(db, as_of=datetime.date(2026, 5, 10))
    assert count == 1
    assert sub_auto.status == "closed"
    assert sub_manual.status == "active"  # Remains active for upcoming renewals


def test_flag_upcoming_renewals_job(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Active sub expiring in 15 days (2026-05-16) as of 2026-05-01
    sub_soon = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="active",
        start_date=datetime.date(2025, 5, 16),
        expiry_date=datetime.date(2026, 5, 16),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    # Active sub expiring in 60 days (2026-07-01)
    sub_far = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="active",
        start_date=datetime.date(2025, 7, 1),
        expiry_date=datetime.date(2026, 7, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )

    count = flag_upcoming_renewals(db, as_of=datetime.date(2026, 5, 1))
    assert count == 1
    assert sub_soon.renewal_flagged_at is not None
    assert sub_far.renewal_flagged_at is None
