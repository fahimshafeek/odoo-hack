import uuid
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Date,
    Numeric,
    Integer,
    ForeignKey,
    CheckConstraint,
    Index,
    JSON,
)
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.clock import now
# Ensure models are registered in registry
import app.catalog.models  # noqa: F401
import app.core.models  # noqa: F401


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("expiry_date > start_date", name="ck_subscriptions_expiry_after_start"),
        CheckConstraint(
            "status IN ('draft', 'quotation', 'confirmed', 'active', 'paused', 'closed')",
            name="ck_subscriptions_status_enum",
        ),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_customer_id", "customer_id"),
        Index("ix_subscriptions_plan_id", "plan_id"),
        Index(
            "ix_subscriptions_active_billing",
            "next_billing_date",
            sqlite_where=Column("status") == "active",
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    plan_id = Column(Uuid(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    payment_term_id = Column(Uuid(as_uuid=True), ForeignKey("payment_terms.id"), nullable=False)
    next_billing_date = Column(Date, nullable=True)
    quotation_template_id = Column(Uuid(as_uuid=True), ForeignKey("quotation_templates.id"), nullable=True)
    quote_valid_until = Column(Date, nullable=True)
    renewal_flagged_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    plan = relationship("Plan", lazy="raise")
    payment_term = relationship("PaymentTerm", lazy="raise")
    customer = relationship("Customer", lazy="raise")
    template = relationship("QuotationTemplate", lazy="raise")
    created_by_user = relationship("User", lazy="raise")

    lines = relationship(
        "SubscriptionLine",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionLine.position",
        lazy="raise",
    )
    history = relationship(
        "SubscriptionHistory",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionHistory.changed_at.desc()",
        lazy="raise",
    )


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_subscription_lines_quantity_ge_1"),
        CheckConstraint("unit_price >= 0", name="ck_subscription_lines_unit_price_non_negative"),
        CheckConstraint("amount >= 0", name="ck_subscription_lines_amount_non_negative"),
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="ck_subscription_lines_tax_rate_range"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant = Column(JSON, nullable=False, default=dict)  # {"selections": [{"attribute": ..., "value": ..., "extra_price": ...}]}
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_id = Column(Uuid(as_uuid=True), ForeignKey("taxes.id"), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))  # qty * unit_price
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    subscription = relationship("Subscription", back_populates="lines", lazy="raise")
    product = relationship("Product", lazy="raise")
    tax = relationship("Tax", lazy="raise")


class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    from_status = Column(String(20), nullable=False)
    to_status = Column(String(20), nullable=False)
    action = Column(String(30), nullable=False)
    changed_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=now)
    note = Column(String(500), nullable=True)

    subscription = relationship("Subscription", back_populates="history", lazy="raise")
    changed_by_user = relationship("User", lazy="raise")
