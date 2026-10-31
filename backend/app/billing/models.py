import uuid
from datetime import date, datetime
from decimal import Decimal
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
from app.core.clock import now
from app.core.db import Base
from app.catalog.models import Tax
from app.payments.models import Payment


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

    targets: Mapped[list["DiscountTarget"]] = relationship(
        "DiscountTarget",
        back_populates="discount",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    redemptions: Mapped[list["DiscountRedemption"]] = relationship(
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
        Uuid,
        ForeignKey("discounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    discount: Mapped[Discount] = relationship("Discount", back_populates="targets")

    __table_args__ = (
        CheckConstraint(
            "(product_id IS NOT NULL AND subscription_id IS NULL) OR (product_id IS NULL AND subscription_id IS NOT NULL)",
            name="ck_discount_targets_target_check",
        ),
        UniqueConstraint(
            "discount_id", "product_id", name="uq_discount_targets_discount_product"
        ),
        UniqueConstraint(
            "discount_id",
            "subscription_id",
            name="uq_discount_targets_discount_subscription",
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
        Uuid,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, nullable=False
    )

    discount: Mapped[Discount] = relationship("Discount", back_populates="redemptions")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="redemptions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_discount_redemptions_amount_positive"),
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

    billing_run: Mapped["BillingRun | None"] = relationship(
        "BillingRun", back_populates="invoices", lazy="selectin"
    )
    lines: Mapped[list["InvoiceLine"]] = relationship(
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
        Uuid,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # plan_fee | product
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("discounts.id", ondelete="SET NULL"), nullable=True
    )
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

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")
    discount: Mapped[Discount | None] = relationship("Discount", lazy="selectin")

    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_invoice_lines_quantity_positive"),
        CheckConstraint(
            "unit_price >= 0", name="ck_invoice_lines_unit_price_non_negative"
        ),
        CheckConstraint(
            "gross_amount >= 0", name="ck_invoice_lines_gross_amount_non_negative"
        ),
        CheckConstraint(
            "discount_amount >= 0 AND discount_amount <= gross_amount",
            name="ck_invoice_lines_discount_bounds",
        ),
        CheckConstraint(
            "tax_rate >= 0 AND tax_rate <= 100",
            name="ck_invoice_lines_tax_rate_range",
        ),
        CheckConstraint(
            "tax_amount >= 0", name="ck_invoice_lines_tax_amount_non_negative"
        ),
        CheckConstraint(
            "line_total >= 0", name="ck_invoice_lines_line_total_non_negative"
        ),
        CheckConstraint(
            "line_type IN ('plan_fee', 'product')", name="ck_invoice_lines_type_enum"
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
