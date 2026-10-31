import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.auth.models import Customer, User
from app.billing.models import Invoice
from app.catalog.models import Plan
from app.core.cache import cached
from app.core.clock import today
from app.core.money import format_money, q2
from app.core.pagination import PageParams, paginate
from app.payments.models import Payment
from app.reports.schemas import (
    MonthlyRevenueItem,
    OverdueInvoiceItem,
    ReportSummaryOut,
    UpcomingRenewalItem,
)
from app.subscriptions.models import Subscription, SubscriptionLine

@cached("reports_summary", ttl_seconds=30)
def get_reports_summary(
    session: Session,
    as_of: date | None = None
) -> ReportSummaryOut:
    curr_date = as_of or today()

    # 1. Active Subscriptions count
    active_subs_count = session.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    ) or 0

    # 2. MRR (Monthly Recurring Revenue) Calculation
    # Monthly equivalent for each active subscription's plan price + lines
    active_subs = session.scalars(
        select(Subscription).where(Subscription.status == "active")
    ).all()

    total_mrr = Decimal("0.00")
    for sub in active_subs:
        plan_period = sub.plan.billing_period if sub.plan else "monthly"
        base_fee = sub.plan.price if sub.plan else Decimal("0.00")
        lines_sum = sum((line.amount for line in sub.lines), Decimal("0.00"))
        period_amount = base_fee + lines_sum

        if plan_period == "daily":
            monthly_equiv = period_amount * Decimal("30")
        elif plan_period == "weekly":
            monthly_equiv = period_amount * (Decimal("52") / Decimal("12"))
        elif plan_period == "yearly":
            monthly_equiv = period_amount / Decimal("12")
        else:  # monthly
            monthly_equiv = period_amount

        total_mrr += monthly_equiv

    # 3. Revenue Collected (Total Payments in current month)
    first_of_month = curr_date.replace(day=1)
    revenue_collected = session.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.paid_on >= first_of_month)
    ) or Decimal("0.00")

    # 4. Invoiced Total (Confirmed/Paid in current month)
    invoiced_total = session.scalar(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(
            Invoice.status.in_(["confirmed", "paid"]),
            Invoice.issue_date >= first_of_month,
        )
    ) or Decimal("0.00")

    # 5. Outstanding Total (Confirmed invoices with unpaid balance)
    outstanding_invoices = session.scalars(
        select(Invoice).where(Invoice.status == "confirmed")
    ).all()
    outstanding_total = sum(
        (inv.total - inv.amount_paid for inv in outstanding_invoices if (inv.total - inv.amount_paid) > 0),
        Decimal("0.00")
    )

    # 6. Overdue Count & Total (Confirmed, balance > 0, due_date < today)
    overdue_invoices = [
        inv for inv in outstanding_invoices
        if inv.due_date < curr_date and (inv.total - inv.amount_paid) > 0
    ]
    overdue_count = len(overdue_invoices)
    overdue_total = sum((inv.total - inv.amount_paid for inv in overdue_invoices), Decimal("0.00"))

    # 7. Upcoming renewals (Active subscriptions expiring in next 30 days)
    thirty_days_later = curr_date + timedelta(days=30)
    upcoming_renewals = session.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == "active",
            Subscription.expiry_date >= curr_date,
            Subscription.expiry_date <= thirty_days_later,
        )
    ) or 0

    return ReportSummaryOut(
        as_of=curr_date,
        active_subscriptions=active_subs_count,
        mrr=format_money(q2(total_mrr)),
        revenue_collected=format_money(Decimal(str(revenue_collected))),
        invoiced_total=format_money(Decimal(str(invoiced_total))),
        outstanding_total=format_money(q2(outstanding_total)),
        overdue_count=overdue_count,
        overdue_total=format_money(q2(overdue_total)),
        upcoming_renewals_count=upcoming_renewals,
    )

@cached("revenue_by_month", ttl_seconds=30)
def get_revenue_by_month(session: Session, months: int = 12) -> list[MonthlyRevenueItem]:
    """Generates monthly aggregated invoiced vs collected revenue."""
    curr_date = today()
    result = []

    for i in range(months - 1, -1, -1):
        # Calculate year and month for the slice
        year = curr_date.year
        month = curr_date.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_str = f"{year:04d}-{month:02d}"
        m_start = date(year, month, 1)
        if month == 12:
            m_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(year, month + 1, 1) - timedelta(days=1)

        invoiced = session.scalar(
            select(func.coalesce(func.sum(Invoice.total), 0)).where(
                Invoice.status.in_(["confirmed", "paid"]),
                Invoice.issue_date >= m_start,
                Invoice.issue_date <= m_end,
            )
        ) or Decimal("0.00")

        collected = session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.paid_on >= m_start,
                Payment.paid_on <= m_end,
            )
        ) or Decimal("0.00")

        result.append(
            MonthlyRevenueItem(
                month=month_str,
                invoiced=format_money(Decimal(str(invoiced))),
                collected=format_money(Decimal(str(collected))),
            )
        )

    return result

def get_overdue_invoices(session: Session, params: PageParams) -> tuple[list[OverdueInvoiceItem], int]:
    curr_date = today()
    stmt = (
        select(Invoice)
        .where(
            Invoice.status == "confirmed",
            Invoice.due_date < curr_date,
            (Invoice.total - Invoice.amount_paid) > 0,
        )
        .order_by(Invoice.due_date.asc())
    )

    items, total = paginate(session, stmt, params)
    out_items = []
    for inv in items:
        cust = inv.customer
        user = cust.user if cust else None
        cust_name = (cust.company_name if cust and cust.company_name else (user.full_name if user else "Unknown"))
        phone = cust.phone if cust else None
        days = (curr_date - inv.due_date).days
        bal = inv.total - inv.amount_paid

        out_items.append(
            OverdueInvoiceItem(
                invoice_id=inv.id,
                number=inv.number,
                customer_id=inv.customer_id,
                customer_name=cust_name,
                phone=phone,
                due_date=inv.due_date,
                days_overdue=days,
                total=format_money(inv.total),
                balance=format_money(bal),
            )
        )
    return out_items, total

def get_upcoming_renewals(session: Session, params: PageParams, days: int = 30) -> tuple[list[UpcomingRenewalItem], int]:
    curr_date = today()
    max_date = curr_date + timedelta(days=days)

    stmt = (
        select(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.expiry_date >= curr_date,
            Subscription.expiry_date <= max_date,
        )
        .order_by(Subscription.expiry_date.asc())
    )

    items, total = paginate(session, stmt, params)
    out_items = []
    for sub in items:
        cust = sub.customer
        user = cust.user if cust else None
        cust_name = (cust.company_name if cust and cust.company_name else (user.full_name if user else "Unknown"))
        plan_name = sub.plan.name if sub.plan else "Standard"
        days_left = (sub.expiry_date - curr_date).days
        allow_renew = sub.plan.allow_renew if sub.plan else True

        out_items.append(
            UpcomingRenewalItem(
                subscription_id=sub.id,
                number=sub.number,
                customer_name=cust_name,
                plan_name=plan_name,
                expiry_date=sub.expiry_date,
                days_left=days_left,
                allow_renew=allow_renew,
            )
        )
    return out_items, total

def sanitize_csv_cell(val: str | None) -> str:
    """Protects against spreadsheet formula injection (=, +, -, @)."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.startswith(("=", "+", "-", "@")):
        return f"'{s}"
    return s

def export_csv_stream(session: Session, report_type: str) -> io.StringIO:
    """Generates an in-memory CSV stream with injection safety."""
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "overdue":
        writer.writerow(["Invoice Number", "Customer", "Phone", "Due Date", "Days Overdue", "Total (INR)", "Balance Due (INR)"])
        items, _ = get_overdue_invoices(session, PageParams(page=1, page_size=1000))
        for item in items:
            writer.writerow([
                sanitize_csv_cell(item.number),
                sanitize_csv_cell(item.customer_name),
                sanitize_csv_cell(item.phone),
                sanitize_csv_cell(str(item.due_date)),
                sanitize_csv_cell(str(item.days_overdue)),
                sanitize_csv_cell(item.total),
                sanitize_csv_cell(item.balance),
            ])
    elif report_type == "upcoming_renewals":
        writer.writerow(["Subscription Number", "Customer", "Plan", "Expiry Date", "Days Left", "Allow Renew"])
        items, _ = get_upcoming_renewals(session, PageParams(page=1, page_size=1000))
        for item in items:
            writer.writerow([
                sanitize_csv_cell(item.number),
                sanitize_csv_cell(item.customer_name),
                sanitize_csv_cell(item.plan_name),
                sanitize_csv_cell(str(item.expiry_date)),
                sanitize_csv_cell(str(item.days_left)),
                sanitize_csv_cell(str(item.allow_renew)),
            ])
    else:
        # Default subscriptions export
        writer.writerow(["Subscription ID", "Number", "Customer ID", "Status", "Start Date", "Expiry Date"])
        subs = session.scalars(select(Subscription).limit(1000)).all()
        for sub in subs:
            writer.writerow([
                sanitize_csv_cell(sub.id),
                sanitize_csv_cell(sub.number),
                sanitize_csv_cell(sub.customer_id),
                sanitize_csv_cell(sub.status),
                sanitize_csv_cell(str(sub.start_date)),
                sanitize_csv_cell(str(sub.expiry_date)),
            ])

    output.seek(0)
    return output
