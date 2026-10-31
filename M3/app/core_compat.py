"""
Core compatibility helpers for M3:
Money formatting, rounding, dates, error classes, sequences, and security checks.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any, Literal, NamedTuple
from zoneinfo import ZoneInfo

from pydantic import BaseModel, BeforeValidator, PlainSerializer

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


# -----------------------------------------------------------------------------
# Money utilities
# -----------------------------------------------------------------------------
def to_decimal(v: Any) -> Decimal:
    if isinstance(v, float):
        raise ValueError("Float is strictly forbidden for money computation")
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, str)):
        return Decimal(str(v))
    raise TypeError(f"Cannot convert {type(v)} to Decimal")


def q2(x: Decimal) -> Decimal:
    """Quantize to 2 decimal places using ROUND_HALF_UP."""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def tax_amount(net: Decimal, rate_percent: Decimal) -> Decimal:
    """Compute tax on net amount at rate_percent, quantized half-up."""
    return q2((net * rate_percent) / Decimal(100))


def _validate_money(v: Any) -> Decimal:
    d = to_decimal(v)
    if d.as_tuple().exponent < -2:
        raise ValueError("Money value cannot have more than 2 decimal places")
    return d


def _serialize_money(v: Decimal) -> str:
    return f"{v:.2f}"


Money = Annotated[
    Decimal,
    BeforeValidator(_validate_money),
    PlainSerializer(_serialize_money, return_type=str),
]


# -----------------------------------------------------------------------------
# Clock
# -----------------------------------------------------------------------------
def today() -> date:
    """Current date in Asia/Kolkata timezone."""
    return datetime.now(KOLKATA_TZ).date()


def now() -> datetime:
    """Current UTC datetime with timezone."""
    return datetime.now(UTC)


# -----------------------------------------------------------------------------
# Errors
# -----------------------------------------------------------------------------
class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        fields: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "fields": self.fields,
            }
        }


# -----------------------------------------------------------------------------
# Auth & RBAC
# -----------------------------------------------------------------------------
class AuthUser(BaseModel):
    id: uuid.UUID
    email: str
    role: Literal["admin", "staff", "customer"]
    customer_id: uuid.UUID | None = None
    full_name: str = ""


def require_role(*roles: str):
    def dependency(user: AuthUser) -> AuthUser:
        if user.role not in roles:
            raise AppError("forbidden", "Insufficient permissions", status=403)
        return user

    return dependency


def scope_to_customer(stmt, customer_id_col, user: AuthUser):
    if user.role == "customer":
        return stmt.where(customer_id_col == user.customer_id)
    return stmt


def assert_customer_owns(user: AuthUser, customer_id: uuid.UUID | None) -> None:
    if user.role == "customer" and user.customer_id != customer_id:
        raise AppError("not_found", "Resource not found", status=404)


# -----------------------------------------------------------------------------
# Email & Cache
# -----------------------------------------------------------------------------
class Attachment(NamedTuple):
    filename: str
    content: bytes
    mime_type: str


_sent_emails: list[dict[str, Any]] = []


def send_email(
    *,
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
    attachments: Sequence[Attachment] = (),
) -> None:
    _sent_emails.append(
        {
            "to": to,
            "subject": subject,
            "html": html,
            "text": text,
            "attachments": list(attachments),
        }
    )


_invalidated_prefixes: list[str] = []


def invalidate(prefix: str = "") -> None:
    _invalidated_prefixes.append(prefix)


def cached(key: str, ttl_seconds: int = 30):
    def decorator(fn):
        return fn

    return decorator


# -----------------------------------------------------------------------------
# SQL Expressions for Invoice balance and overdue
# -----------------------------------------------------------------------------
def balance_expr(total_col, amount_paid_col):
    return total_col - amount_paid_col


def is_overdue_expr(due_date_col, status_col, balance_expr_col, today_val: date):
    return (
        (status_col == "confirmed")
        & (balance_expr_col > 0)
        & (due_date_col < today_val)
    )


# -----------------------------------------------------------------------------
# Billing Period
# -----------------------------------------------------------------------------
class BillingPeriod(NamedTuple):
    start: date
    end: date
    next_billing_date: date
