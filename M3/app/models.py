"""
SQLAlchemy ORM models for M3: Billing & Payments (SQLite compatible).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core_compat import now, today
from app.database import Base


class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g. "INV-2026"
    last_seq: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


def next_number(session, kind: Literal["SUB", "INV"], on: date | None = None) -> str:
    target_date = on or today()
    year = target_date.year
    prefix = f"{kind}-{year}"

    seq_row = session.get(DocumentSequence, prefix)
    if not seq_row:
        seq_row = DocumentSequence(id=prefix, last_seq=1)
        session.add(seq_row)
        session.flush()
        return f"{prefix}-{1:06d}"
    else:
        seq_row.last_seq += 1
        session.flush()
        return f"{prefix}-{seq_row.last_seq:06d}"


class Tax(Base):
    __tablename__ = "taxes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "rate_percent >= 0 AND rate_percent <= 100",
            name="ck_taxes_rate_percent_range",
        ),
    )


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # fixed | percent
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # product | subscription
    min_purchase: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, nullable=False
    )

    targets: Mapped[list[DiscountTarget]] = relationship(
        "DiscountTarget",
        back_populates="discount",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    redemptions: Mapped[list[DiscountRedemption]] = relationship(
        "DiscountRedemption",
        back_populates="discount",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("value > 0", name="ck_discounts_value_positive"),
        CheckConstraint(
            "(type = 'percent' AND value <= 100) OR (type = 'fixed')",
            name="ck_discounts_percent_max",
        ),
        CheckConstraint("end_date >= start_date", name="ck_discounts_end_after_start"),
        CheckConstraint(
            "usage_limit IS NULL OR usage_limit >= 1",
            name="ck_discounts_usage_limit_positive",
        ),
        CheckConstraint(
            "min_purchase IS NULL OR min_purchase >= 0",
            name="ck_discounts_min_purchase_positive",
        ),
        CheckConstraint(
            "min_quantity IS NULL OR min_quantity >= 0",
            name="ck_discounts_min_quantity_positive",
        ),
    )


class DiscountTarget(Base):
    __tablename__ = "discount_targets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    discount_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("discounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    discount: Mapped[Discount] = relationship(
        "Discount", back_populates="targets", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "(product_id IS NOT NULL AND subscription_id IS NULL) OR "
            "(product_id IS NULL AND subscription_id IS NOT NULL)",
            name="ck_discount_targets_exclusive",
        ),
        UniqueConstraint(
            "discount_id",
            "product_id",
            "subscription_id",
            name="uq_discount_targets_pair",
        ),
    )


class DiscountRedemption(Base):
    __tablename__ = "discount_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    discount_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("discounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    discount: Mapped[Discount] = relationship(
        "Discount", back_populates="redemptions", lazy="selectin"
    )
    invoice: Mapped[Invoice] = relationship(
        "Invoice", back_populates="redemptions", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "discount_id", "invoice_id", name="uq_discount_redemptions_discount_invoice"
        ),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    billing_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("billing_runs.id"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discount_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, nullable=False
    )

    billing_run: Mapped[BillingRun | None] = relationship(
        "BillingRun", back_populates="invoices", lazy="selectin"
    )
    lines: Mapped[list[InvoiceLine]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.position",
    )
    redemptions: Mapped[list[DiscountRedemption]] = relationship(
        "DiscountRedemption",
        back_populates="invoice",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list[Payment]] = relationship(
        "Payment",
        back_populates="invoice",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "subscription_id", "period_start", name="uq_invoices_subscription_period"
        ),
        CheckConstraint("total >= 0", name="ck_invoices_total_non_negative"),
        CheckConstraint(
            "amount_paid >= 0 AND amount_paid <= total",
            name="ck_invoices_amount_paid_bounds",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'paid', 'cancelled')",
            name="ck_invoices_status_enum",
        ),
        Index("ix_invoices_status_due_date", "status", "due_date"),
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # plan_fee | product
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    discount_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    invoice: Mapped[Invoice] = relationship(
        "Invoice", back_populates="lines", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_invoice_lines_quantity_min_one"),
        CheckConstraint("gross_amount >= 0", name="ck_invoice_lines_gross_positive"),
        CheckConstraint("line_total >= 0", name="ck_invoice_lines_line_total_positive"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    method: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # cash|bank_transfer|card|upi|cheque|online
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, nullable=False
    )

    invoice: Mapped[Invoice] = relationship(
        "Invoice", back_populates="payments", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        CheckConstraint(
            "method IN ('cash', 'bank_transfer', 'card', 'upi', 'cheque', 'online')",
            name="ck_payments_method_enum",
        ),
    )


class BillingRun(Base):
    __tablename__ = "billing_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="running", nullable=False
    )  # running | finished | failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    total_due: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )

    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice", back_populates="billing_run", lazy="selectin"
    )


# -----------------------------------------------------------------------------
# SubscriptionStub (Internal test/execution model for subscriptions in SQLite)
# -----------------------------------------------------------------------------
class SubscriptionStub(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # draft|quotation|confirmed|active|paused|closed
    billing_period: Mapped[str] = mapped_column(
        String(20), default="monthly", nullable=False
    )  # daily|weekly|monthly|yearly
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    plan_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    plan_tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    due_days: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )  # from payment term

    lines: Mapped[list[SubscriptionLineStub]] = relationship(
        "SubscriptionLineStub",
        back_populates="subscription",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class SubscriptionLineStub(Base):
    __tablename__ = "subscription_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subscription: Mapped[SubscriptionStub] = relationship(
        "SubscriptionStub", back_populates="lines", lazy="selectin"
    )
