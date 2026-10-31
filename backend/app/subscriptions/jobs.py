import datetime
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.clock import today as get_today, now as get_now
from app.subscriptions.models import Subscription
from app.subscriptions.state import transition

logger = logging.getLogger("brightloop.jobs.subscriptions")


def activate_due(session, as_of: Optional[datetime.date] = None) -> int:
    """Activate confirmed subscriptions where start_date <= as_of."""
    target_date = as_of or get_today()
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.lines))
        .where(
            Subscription.status == "confirmed",
            Subscription.start_date <= target_date,
        )
        .limit(500)
    )
    subs = session.execute(stmt).scalars().all()
    count = 0
    for sub in subs:
        transition(session, sub, "activate", user=None, note="Activated by scheduled lifecycle job")
        count += 1
    session.flush()
    logger.info("activate_due processed %d subscriptions as_of %s", count, target_date)
    return count


def expire_quotes(session, as_of: Optional[datetime.date] = None) -> int:
    """Close quotations where quote_valid_until < as_of."""
    target_date = as_of or get_today()
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.lines))
        .where(
            Subscription.status == "quotation",
            Subscription.quote_valid_until.is_not(None),
            Subscription.quote_valid_until < target_date,
        )
        .limit(500)
    )
    subs = session.execute(stmt).scalars().all()
    count = 0
    for sub in subs:
        transition(session, sub, "expire-quote", user=None, note=f"Quote expired as of {target_date}")
        count += 1
    session.flush()
    logger.info("expire_quotes closed %d quotations as_of %s", count, target_date)
    return count


def auto_close_expired(session, as_of: Optional[datetime.date] = None) -> int:
    """Close active subscriptions past expiry_date if plan.auto_close is True."""
    target_date = as_of or get_today()
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.lines))
        .where(
            Subscription.status == "active",
            Subscription.expiry_date < target_date,
        )
        .limit(500)
    )
    subs = session.execute(stmt).scalars().all()
    count = 0
    for sub in subs:
        if sub.plan and sub.plan.auto_close:
            transition(session, sub, "auto-close", user=None, note=f"Auto-closed past expiry {sub.expiry_date}")
            count += 1
    session.flush()
    logger.info("auto_close_expired closed %d subscriptions as_of %s", count, target_date)
    return count


def flag_upcoming_renewals(session, as_of: Optional[datetime.date] = None) -> int:
    """Flag active subscriptions expiring within 30 days that have not yet been flagged."""
    target_date = as_of or get_today()
    window_end = target_date + datetime.timedelta(days=30)
    stmt = (
        select(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.expiry_date >= target_date,
            Subscription.expiry_date <= window_end,
            Subscription.renewal_flagged_at.is_(None),
        )
        .limit(500)
    )
    subs = session.execute(stmt).scalars().all()
    now_time = get_now()
    count = 0
    for sub in subs:
        sub.renewal_flagged_at = now_time
        count += 1
    session.flush()
    logger.info("flag_upcoming_renewals flagged %d subscriptions as_of %s", count, target_date)
    return count


def register(scheduler) -> None:
    """Register cron jobs with scheduler at canonical times (A5 schedule)."""
    if scheduler is None:
        return
    # 01:00 activate
    scheduler.add_job(lambda: activate_due, "cron", hour=1, minute=0, id="activate_due")
    # 01:15 expire quotes
    scheduler.add_job(lambda: expire_quotes, "cron", hour=1, minute=15, id="expire_quotes")
    # 01:30 auto-close
    scheduler.add_job(lambda: auto_close_expired, "cron", hour=1, minute=30, id="auto_close_expired")
    # 02:30 renewal flag
    scheduler.add_job(lambda: flag_upcoming_renewals, "cron", hour=2, minute=30, id="flag_upcoming_renewals")
