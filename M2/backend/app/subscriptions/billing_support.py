import calendar
import datetime
import uuid
from dataclasses import dataclass
from typing import Optional, Collection, List
from sqlalchemy import select, func
from app.subscriptions.models import Subscription


@dataclass(frozen=True)
class BillingPeriod:
    start: datetime.date
    end: datetime.date
    next_billing_date: datetime.date


def add_period(d: datetime.date, period: str, anchor_day: int) -> datetime.date:
    """
    Pure anchor-day logic for computing the next period anniversary.
    Anchor-day rules:
    - daily: +1 day
    - weekly: +7 days
    - monthly: next month, clamped to month's end using anchor_day (e.g. 31 Jan -> 28 Feb -> 31 Mar)
    - yearly: next year, clamped to month's end using anchor_day (e.g. 29 Feb 2024 -> 28 Feb 2025)
    """
    if period == "daily":
        return d + datetime.timedelta(days=1)
    if period == "weekly":
        return d + datetime.timedelta(days=7)
    if period == "monthly":
        if d.month == 12:
            target_year = d.year + 1
            target_month = 1
        else:
            target_year = d.year
            target_month = d.month + 1
        max_days = calendar.monthrange(target_year, target_month)[1]
        day = min(anchor_day, max_days)
        return datetime.date(target_year, target_month, day)
    if period == "yearly":
        target_year = d.year + 1
        target_month = d.month
        max_days = calendar.monthrange(target_year, target_month)[1]
        day = min(anchor_day, max_days)
        return datetime.date(target_year, target_month, day)

    raise ValueError(f"Unknown billing period: {period}")


def next_period(sub: Subscription) -> Optional[BillingPeriod]:
    """
    Compute next billing period for an active subscription.
    Returns None if next_billing_date is None or exceeds sub.expiry_date.
    Clamps period_end to sub.expiry_date.
    """
    if sub.next_billing_date is None or sub.next_billing_date > sub.expiry_date:
        return None

    period_start = sub.next_billing_date
    anchor_day = sub.start_date.day
    period_type = sub.plan.billing_period if hasattr(sub, "plan") and sub.plan else "monthly"

    next_anniversary = add_period(period_start, period_type, anchor_day)
    period_end = next_anniversary - datetime.timedelta(days=1)

    # Clamp to expiry_date
    if period_end > sub.expiry_date:
        period_end = sub.expiry_date

    # Period's next_billing_date is period_end + 1 day
    next_bill_date = period_end + datetime.timedelta(days=1)

    return BillingPeriod(
        start=period_start,
        end=period_end,
        next_billing_date=next_bill_date,
    )


def advance_next_billing_date(sub: Subscription, period: BillingPeriod) -> None:
    """Sets sub.next_billing_date = period.next_billing_date."""
    sub.next_billing_date = period.next_billing_date


def count_due(session, as_of: datetime.date) -> int:
    """Count active subscriptions due for billing on or before as_of date."""
    stmt = (
        select(func.count(Subscription.id))
        .where(
            Subscription.status == "active",
            Subscription.next_billing_date.is_not(None),
            Subscription.next_billing_date <= as_of,
            Subscription.next_billing_date <= Subscription.expiry_date,
        )
    )
    return session.execute(stmt).scalar() or 0


def due_subscriptions(
    session,
    as_of: datetime.date,
    *,
    limit: int = 200,
    exclude_ids: Collection[uuid.UUID] = (),
) -> List[Subscription]:
    """
    Fetch active subscriptions due for billing on or before as_of date.
    Ordered by next_billing_date, id.
    Uses FOR UPDATE SKIP LOCKED on engines that support it (PostgreSQL).
    """
    stmt = (
        select(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.next_billing_date.is_not(None),
            Subscription.next_billing_date <= as_of,
            Subscription.next_billing_date <= Subscription.expiry_date,
        )
        .order_by(Subscription.next_billing_date.asc(), Subscription.id.asc())
        .limit(limit)
    )

    if exclude_ids:
        stmt = stmt.where(Subscription.id.not_in(exclude_ids))

    dialect = session.bind.dialect.name if session.bind else ""
    if dialect not in ("sqlite", ""):
        stmt = stmt.with_for_update(skip_locked=True)

    return list(session.execute(stmt).scalars().all())
