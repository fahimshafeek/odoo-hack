"""Compatibility module re-exporting core utilities for legacy M3 tests and references."""
from datetime import date
from app.core.clock import now, today, KOLKATA_TZ
from app.core.money import q2, to_decimal, tax_amount, format_money, Money
from app.core.errors import AppError
from app.core.deps import AuthUser, assert_customer_owns, require_role
from app.core.cache import cached, invalidate
from app.core.mail import Attachment, send_email
from app.billing.engine import BillingPeriod
from app.billing.tax import compute_tax

format_currency = format_money


def balance_expr(total_col, amount_paid_col):
    return total_col - amount_paid_col


def is_overdue_expr(due_date_col, status_col, balance_expr_col, today_val: date):
    return (
        (status_col == "confirmed")
        & (balance_expr_col > 0)
        & (due_date_col < today_val)
    )
