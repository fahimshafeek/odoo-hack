"""
Billing engine orchestrator for M3 (INV-1, INV-5, plan 9.3, D15, D18).
Guarantees:
  - 'Never billed twice, never skipped'
  - Savepoint isolation with discount claim rollback on duplicate period
  - Multi-period catch-up (e.g. 3 daily periods catch up to 3 invoices)
  - Period clamped to expiry_date
"""

from __future__ import annotations

import calendar
import logging
import uuid
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.billing.calc import LineInput, calculate_invoice_lines
from app.core.clock import now, today
from app.core.cache import invalidate
from app.core.numbering import next_number
from app.billing.discounts import run_discount_claim_loop
from app.billing.models import (
    BillingRun,
    DiscountRedemption,
    Invoice,
    InvoiceLine,
)
from app.subscriptions.models import Subscription

from typing import Callable, NamedTuple

# Compatibility alias
SubscriptionStub = Subscription

logger = logging.getLogger(__name__)


class BillingPeriod(NamedTuple):
    start: date
    end: date
    next_billing_date: date



def compute_next_period(
    start_date: date,
    billing_period: str,
    expiry_date: date,
) -> BillingPeriod | None:
    """
    Calculates next period [start, end] and next_billing_date.
    Returns None if start_date > expiry_date.
    End date is clamped to expiry_date.
    """
    if start_date > expiry_date:
        return None

    if billing_period == "daily":
        end_date = start_date
        next_start = start_date + timedelta(days=1)
    elif billing_period == "weekly":
        end_date = start_date + timedelta(days=6)
        next_start = start_date + timedelta(days=7)
    elif billing_period == "monthly":
        # Advance 1 month
        month = start_date.month + 1
        year = start_date.year
        if month > 12:
            month = 1
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        next_day = min(start_date.day, max_day)
        next_start = date(year, month, next_day)
        end_date = next_start - timedelta(days=1)
    elif billing_period == "yearly":
        try:
            next_start = date(start_date.year + 1, start_date.month, start_date.day)
        except ValueError:
            # Leap day 29 Feb -> 28 Feb
            next_start = date(start_date.year + 1, start_date.month, 28)
        end_date = next_start - timedelta(days=1)
    else:
        # Default monthly
        next_start = start_date + timedelta(days=30)
        end_date = next_start - timedelta(days=1)

    # Clamp end date to expiry
    end_date = min(end_date, expiry_date)

    return BillingPeriod(start=start_date, end=end_date, next_billing_date=next_start)


def count_due_subscriptions(session: Session, as_of: date) -> int:
    """Counts active subscriptions due for billing on or before as_of."""
    stmt = select(func.count(SubscriptionStub.id)).where(
        SubscriptionStub.status == "active",
        SubscriptionStub.next_billing_date <= as_of,
        SubscriptionStub.next_billing_date <= SubscriptionStub.expiry_date,
    )
    return session.scalar(stmt) or 0


def create_run(
    session: Session, as_of: date, triggered_by: uuid.UUID | None = None
) -> BillingRun:
    """Inserts a new BillingRun record in status='running'."""
    total_due = count_due_subscriptions(session, as_of)
    run_record = BillingRun(
        run_date=as_of,
        status="running",
        started_at=now(),
        total_due=total_due,
        processed=0,
        created_count=0,
        skipped_count=0,
        failed_count=0,
        triggered_by=triggered_by,
    )
    session.add(run_record)
    session.commit()
    return run_record


def run_billing(
    session_factory: Callable[[], Session],
    *,
    as_of: date | None = None,
    triggered_by: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """
    Main billing execution engine (INV-1, INV-5).
    Processes due subscriptions in batches, inserts draft invoices, claims discounts,
    advances billing dates, and writes the BillingRun audit summary.
    """
    as_of_date = as_of or today()

    # 1. Initialize or load run record
    session = session_factory()
    try:
        if run_id:
            run_record = session.get(BillingRun, run_id)
        else:
            run_record = create_run(session, as_of_date, triggered_by)
            run_id = run_record.id
    finally:
        session.close()

    total_created = 0
    total_skipped = 0
    total_failed = 0
    failed_sub_ids: set[uuid.UUID] = set()

    batch_session = session_factory()
    try:
        while True:
            # Query next batch of due active subscriptions
            stmt = (
                select(SubscriptionStub)
                .where(
                    SubscriptionStub.status == "active",
                    SubscriptionStub.next_billing_date <= as_of_date,
                    SubscriptionStub.next_billing_date <= SubscriptionStub.expiry_date,
                )
                .order_by(SubscriptionStub.next_billing_date, SubscriptionStub.id)
                .limit(200)
            )
            subs = batch_session.scalars(stmt).all()

            # Filter out any persistently failed subscriptions in this run
            due_subs = [s for s in subs if s.id not in failed_sub_ids]
            if not due_subs:
                break

            for sub in due_subs:
                # Multi-period catch-up loop
                while (
                    sub.next_billing_date <= as_of_date
                    and sub.next_billing_date <= sub.expiry_date
                ):
                    period = compute_next_period(
                        sub.next_billing_date, sub.billing_period, sub.expiry_date
                    )
                    if not period:
                        break

                    # Savepoint isolation
                    sp = batch_session.begin_nested()
                    try:
                        # Build candidate lines
                        input_lines: list[LineInput] = []
                        pos = 0

                        # 1. Plan-fee line if plan_price > 0 (D14)
                        if sub.plan_price > Decimal("0.00"):
                            input_lines.append(
                                LineInput(
                                    line_type="plan_fee",
                                    description="Plan subscription fee",
                                    product_id=None,
                                    quantity=1,
                                    unit_price=sub.plan_price,
                                    tax_rate=sub.plan_tax_rate,
                                    position=pos,
                                )
                            )
                            pos += 1

                        # 2. Product lines from subscription
                        for s_line in sub.lines:
                            input_lines.append(
                                LineInput(
                                    line_type="product",
                                    description=s_line.description,
                                    product_id=s_line.product_id,
                                    quantity=s_line.quantity,
                                    unit_price=s_line.unit_price,
                                    tax_rate=s_line.tax_rate,
                                    position=pos,
                                )
                            )
                            pos += 1

                        # Run discount evaluation and claim loop inside savepoint
                        line_discounts, redemptions = run_discount_claim_loop(
                            batch_session, input_lines, sub.id, as_of_date
                        )

                        # Calculate totals
                        totals = calculate_invoice_lines(input_lines, line_discounts)

                        # Generate unique invoice number
                        inv_number = next_number(batch_session, "INV", on=as_of_date)
                        due_date = as_of_date + timedelta(days=sub.due_days)

                        # Create Invoice
                        invoice = Invoice(
                            number=inv_number,
                            subscription_id=sub.id,
                            customer_id=sub.customer_id,
                            billing_run_id=run_id,
                            status="draft",
                            period_start=period.start,
                            period_end=period.end,
                            issue_date=as_of_date,
                            due_date=due_date,
                            subtotal=totals.subtotal,
                            discount_total=totals.discount_total,
                            tax_total=totals.tax_total,
                            total=totals.total,
                            amount_paid=Decimal("0.00"),
                        )
                        batch_session.add(invoice)
                        batch_session.flush()

                        # Insert invoice lines
                        for c_line in totals.lines:
                            inv_line = InvoiceLine(
                                invoice_id=invoice.id,
                                line_type=c_line.line_type,
                                description=c_line.description,
                                product_id=c_line.product_id,
                                quantity=c_line.quantity,
                                unit_price=c_line.unit_price,
                                gross_amount=c_line.gross_amount,
                                discount_id=c_line.discount_id,
                                discount_amount=c_line.discount_amount,
                                tax_rate=c_line.tax_rate,
                                tax_amount=c_line.tax_amount,
                                line_total=c_line.line_total,
                                position=c_line.position,
                            )
                            batch_session.add(inv_line)

                        # Record discount redemptions
                        for disc_id, r_amt in redemptions:
                            red = DiscountRedemption(
                                discount_id=disc_id,
                                invoice_id=invoice.id,
                                amount=r_amt,
                            )
                            batch_session.add(red)

                        # Advance next_billing_date
                        sub.next_billing_date = period.next_billing_date
                        batch_session.flush()

                        sp.commit()
                        total_created += 1

                    except IntegrityError:
                        # Duplicate period: roll back savepoint (releasing discount claims)
                        sp.rollback()
                        logger.info(
                            f"Subscription {sub.number} period {period.start} already billed; skipping."
                        )
                        # Still advance date past this duplicate period
                        sub.next_billing_date = period.next_billing_date
                        batch_session.flush()
                        total_skipped += 1

                    except Exception as ex:
                        # Failure isolation: roll back savepoint, do not advance, mark failed
                        sp.rollback()
                        logger.error(f"Error billing subscription {sub.number}: {ex}")
                        failed_sub_ids.add(sub.id)
                        total_failed += 1
                        break  # Stop catch-up loop for this failing subscription

            # Commit batch
            batch_session.commit()

        # Update final run audit stats
        run_record = batch_session.get(BillingRun, run_id)
        if run_record:
            run_record.status = "finished"
            run_record.finished_at = now()
            run_record.processed = total_created + total_skipped + total_failed
            run_record.created_count = total_created
            run_record.skipped_count = total_skipped
            run_record.failed_count = total_failed
            batch_session.commit()

        # Invalidate report cache
        invalidate("reports")

    except Exception as ex:
        batch_session.rollback()
        logger.exception(f"Fatal crash in billing run {run_id}: {ex}")
        run_record = batch_session.get(BillingRun, run_id)
        if run_record:
            run_record.status = "failed"
            run_record.finished_at = now()
            run_record.error = str(ex)
            batch_session.commit()
        raise
    finally:
        batch_session.close()

    return run_id
