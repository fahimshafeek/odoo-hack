import datetime
import uuid
from decimal import Decimal
import pytest
from app.core.errors import AppError
from app.core.deps import AuthUser
from app.subscriptions.state import transition, allowed_actions
from tests.factories import (
    create_test_tax,
    create_test_product,
    create_test_plan,
    create_test_payment_term,
    create_test_customer,
    create_test_subscription,
)


def test_transition_draft_to_quotation_and_activate_flow(db):
    tax = create_test_tax(db)
    prod, attr, val = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="draft",
        start_date=datetime.date(2026, 1, 1),
        expiry_date=datetime.date(2027, 1, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    admin_user = AuthUser(id=uuid.uuid4(), email="admin@example.com", role="admin")

    # 1. Draft -> Quotation via send_quote
    transition(db, sub, "send_quote", admin_user)
    assert sub.status == "quotation"
    assert sub.quote_valid_until is not None

    # 2. Quotation -> Confirmed via confirm
    transition(db, sub, "confirm", admin_user)
    assert sub.status == "confirmed"

    # 3. Confirmed -> Active via activate (sets next_billing_date = start_date)
    transition(db, sub, "activate", admin_user)
    assert sub.status == "active"
    assert sub.next_billing_date == sub.start_date


def test_plan_flags_block_actions_for_admin_too(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    # Plan with all rule flags set to False!
    plan = create_test_plan(
        db,
        allow_pause=False,
        allow_renew=False,
        allow_early_close=False,
    )
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)
    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="active",
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    admin_user = AuthUser(id=uuid.uuid4(), email="admin@example.com", role="admin")

    # Attempt Pause -> fails because plan.allow_pause is False
    with pytest.raises(AppError) as exc:
        transition(db, sub, "pause", admin_user)
    assert exc.value.status == 409
    assert exc.value.code == "plan_rule_violation"

    # Attempt Renew -> fails because plan.allow_renew is False
    with pytest.raises(AppError) as exc:
        transition(db, sub, "renew", admin_user)
    assert exc.value.status == 409
    assert exc.value.code == "plan_rule_violation"

    # Attempt Close -> fails because plan.allow_early_close is False
    with pytest.raises(AppError) as exc:
        transition(db, sub, "close", admin_user)
    assert exc.value.status == 409
    assert exc.value.code == "plan_rule_violation"


def test_customer_role_restrictions(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db, allow_pause=True)
    term = create_test_payment_term(db)
    cust, cust_user = create_test_customer(db)

    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="quotation",
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    customer_auth = AuthUser(
        id=cust_user.id,
        email=cust_user.email,
        role="customer",
        customer_id=cust.id,
    )

    # Customer cannot confirm quotation
    with pytest.raises(AppError) as exc:
        transition(db, sub, "confirm", customer_auth)
    assert exc.value.status == 403
    assert exc.value.code == "forbidden"


def test_d16_resume_skips_paused_periods(db, frozen_today):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db, period="monthly", allow_pause=True)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Sub paused with next_billing_date = Jan 1, 2026
    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="paused",
        start_date=datetime.date(2026, 1, 1),
        expiry_date=datetime.date(2027, 1, 1),
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    sub.next_billing_date = datetime.date(2026, 1, 1)

    # Today is March 15, 2026
    frozen_today(datetime.date(2026, 3, 15))
    admin_user = AuthUser(id=uuid.uuid4(), email="admin@example.com", role="admin")

    transition(db, sub, "resume", admin_user)
    assert sub.status == "active"
    # Should advance from Jan 1 -> Feb 1 -> Mar 1 -> Apr 1 (since Apr 1 >= Mar 15)
    assert sub.next_billing_date == datetime.date(2026, 4, 1)

    # Verify history note records "skipped 3 paused period(s)"
    from app.subscriptions.models import SubscriptionHistory
    from sqlalchemy import select
    history_rows = db.execute(select(SubscriptionHistory).where(SubscriptionHistory.subscription_id == sub.id)).scalars().all()
    assert any("skipped 3 paused period(s)" in (h.note or "") for h in history_rows)


def test_d17_renew_extends_expiry_by_one_term(db):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db, allow_renew=True)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # 1-year subscription: 2026-01-01 to 2027-01-01
    start = datetime.date(2026, 1, 1)
    expiry = datetime.date(2027, 1, 1)
    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status="active",
        start_date=start,
        expiry_date=expiry,
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    admin_user = AuthUser(id=uuid.uuid4(), email="admin@example.com", role="admin")

    transition(db, sub, "renew", admin_user)
    assert sub.status == "active"
    # Expiry extended by 1 year (365 days): 2028-01-01
    assert sub.expiry_date == datetime.date(2028, 1, 1)


@pytest.mark.parametrize(
    "initial_status, invalid_action",
    [
        ("draft", "confirm"),
        ("draft", "activate"),
        ("draft", "pause"),
        ("draft", "resume"),
        ("draft", "renew"),
        ("draft", "close"),
        ("quotation", "send_quote"),
        ("quotation", "activate"),
        ("quotation", "pause"),
        ("confirmed", "send_quote"),
        ("confirmed", "confirm"),
        ("confirmed", "pause"),
        ("active", "send_quote"),
        ("active", "confirm"),
        ("active", "activate"),
        ("active", "resume"),
        ("paused", "send_quote"),
        ("paused", "confirm"),
        ("paused", "pause"),
        ("closed", "send_quote"),
        ("closed", "confirm"),
        ("closed", "activate"),
        ("closed", "pause"),
        ("closed", "resume"),
        ("closed", "renew"),
        ("closed", "close"),
    ],
)
def test_illegal_transition_matrix(db, initial_status, invalid_action):
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    sub = create_test_subscription(
        db,
        cust,
        plan,
        term,
        status=initial_status,
        lines=[(prod, 1, Decimal("1000.00"))],
    )
    admin_user = AuthUser(id=uuid.uuid4(), email="admin@example.com", role="admin")

    with pytest.raises(AppError) as exc:
        transition(db, sub, invalid_action, admin_user)
    assert exc.value.status == 409
    assert exc.value.code == "invalid_transition"
