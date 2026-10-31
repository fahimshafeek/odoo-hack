import datetime
import uuid
import pytest
from app.subscriptions.billing_support import (
    add_period,
    next_period,
    advance_next_billing_date,
    count_due,
    due_subscriptions,
    BillingPeriod,
)
from app.subscriptions.models import Subscription
from app.catalog.models import Plan


@pytest.mark.parametrize(
    "start, period, anchor, expected",
    [
        # Monthly anchor tests: 31 Jan -> 28 Feb -> 31 Mar
        (datetime.date(2026, 1, 31), "monthly", 31, datetime.date(2026, 2, 28)),
        (datetime.date(2026, 2, 28), "monthly", 31, datetime.date(2026, 3, 31)),
        (datetime.date(2026, 3, 31), "monthly", 31, datetime.date(2026, 4, 30)),
        (datetime.date(2026, 4, 30), "monthly", 31, datetime.date(2026, 5, 31)),
        # Leap year 2028
        (datetime.date(2028, 1, 31), "monthly", 31, datetime.date(2028, 2, 29)),
        (datetime.date(2028, 2, 29), "monthly", 31, datetime.date(2028, 3, 31)),
        # Daily
        (datetime.date(2026, 6, 15), "daily", 15, datetime.date(2026, 6, 16)),
        # Weekly
        (datetime.date(2026, 6, 15), "weekly", 15, datetime.date(2026, 6, 22)),
        # Yearly non-leap to non-leap
        (datetime.date(2025, 5, 10), "yearly", 10, datetime.date(2026, 5, 10)),
        # Yearly leap to non-leap
        (datetime.date(2024, 2, 29), "yearly", 29, datetime.date(2025, 2, 28)),
    ],
)
def test_add_period_anchor_table_driven(start, period, anchor, expected):
    res = add_period(start, period, anchor)
    assert res == expected


class DummyPlan:
    def __init__(self, billing_period="monthly"):
        self.billing_period = billing_period


class DummySub:
    def __init__(self, start_date, expiry_date, next_billing_date, plan=None):
        self.start_date = start_date
        self.expiry_date = expiry_date
        self.next_billing_date = next_billing_date
        self.plan = plan or DummyPlan()


def test_next_period_monthly_anchor():
    sub = DummySub(
        start_date=datetime.date(2026, 1, 31),
        expiry_date=datetime.date(2027, 1, 31),
        next_billing_date=datetime.date(2026, 1, 31),
        plan=DummyPlan("monthly"),
    )
    period = next_period(sub)
    assert period is not None
    assert period.start == datetime.date(2026, 1, 31)
    # Next anniversary is 28 Feb -> period end is 27 Feb
    assert period.end == datetime.date(2026, 2, 27)
    assert period.next_billing_date == datetime.date(2026, 2, 28)

    # Advance
    advance_next_billing_date(sub, period)
    assert sub.next_billing_date == datetime.date(2026, 2, 28)

    # Next period from 28 Feb
    period2 = next_period(sub)
    assert period2 is not None
    assert period2.start == datetime.date(2026, 2, 28)
    # Next anniversary from 28 Feb using anchor 31 is 31 Mar -> period end is 30 Mar
    assert period2.end == datetime.date(2026, 3, 30)
    assert period2.next_billing_date == datetime.date(2026, 3, 31)


def test_next_period_clamped_to_expiry():
    # Subscription expires mid-period on 2026-02-15
    sub = DummySub(
        start_date=datetime.date(2026, 1, 31),
        expiry_date=datetime.date(2026, 2, 15),
        next_billing_date=datetime.date(2026, 1, 31),
        plan=DummyPlan("monthly"),
    )
    period = next_period(sub)
    assert period is not None
    assert period.start == datetime.date(2026, 1, 31)
    # Clamped to expiry
    assert period.end == datetime.date(2026, 2, 15)
    assert period.next_billing_date == datetime.date(2026, 2, 16)


def test_next_period_after_expiry_returns_none():
    sub = DummySub(
        start_date=datetime.date(2026, 1, 1),
        expiry_date=datetime.date(2026, 12, 31),
        next_billing_date=datetime.date(2027, 1, 1),
        plan=DummyPlan("monthly"),
    )
    period = next_period(sub)
    assert period is None
