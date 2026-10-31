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
from app.core.db import Base
from app.core.clock import now
import app.catalog.models  # noqa: F401
import app.auth.models  # noqa: F401


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
    plan_id = Column(Uuid(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    payment_term_id = Column(Uuid(as_uuid=True), ForeignKey("payment_terms.id"), nullable=True)
    next_billing_date = Column(Date, nullable=True)
    quotation_template_id = Column(Uuid(as_uuid=True), ForeignKey("quotation_templates.id"), nullable=True)
    quote_valid_until = Column(Date, nullable=True)
    renewal_flagged_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    # Cached/override columns for billing execution and compatibility
    _billing_period = Column("billing_period", String(20), nullable=True)
    _plan_price = Column("plan_price", Numeric(12, 2), nullable=True)
    _plan_tax_rate = Column("plan_tax_rate", Numeric(5, 2), nullable=True)
    _due_days = Column("due_days", Integer, nullable=True)

    plan = relationship("Plan", lazy="select")
    payment_term = relationship("PaymentTerm", lazy="select")
    customer = relationship("Customer", lazy="select")
    template = relationship("QuotationTemplate", lazy="select")
    created_by_user = relationship("User", lazy="select")

    lines = relationship(
        "SubscriptionLine",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionLine.position",
        lazy="selectin",
    )
    history = relationship(
        "SubscriptionHistory",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionHistory.changed_at.desc()",
        lazy="selectin",
    )

    @property
    def billing_period(self) -> str:
        if self._billing_period is not None:
            return self._billing_period
        return self.plan.billing_period if self.plan else "monthly"

    @billing_period.setter
    def billing_period(self, val: str) -> None:
        self._billing_period = val

    @property
    def plan_price(self) -> Decimal:
        if self._plan_price is not None:
            return self._plan_price
        return self.plan.price if self.plan else Decimal("0.00")

    @plan_price.setter
    def plan_price(self, val: Decimal) -> None:
        self._plan_price = val

    @property
    def plan_tax_rate(self) -> Decimal:
        if self._plan_tax_rate is not None:
            return self._plan_tax_rate
        if self.plan and self.plan.tax:
            return self.plan.tax.rate_percent
        return Decimal("0.00")

    @plan_tax_rate.setter
    def plan_tax_rate(self, val: Decimal) -> None:
        self._plan_tax_rate = val

    @property
    def due_days(self) -> int:
        if self._due_days is not None:
            return self._due_days
        if self.payment_term and hasattr(self.payment_term, "days"):
            return self.payment_term.days
        return 15

    @due_days.setter
    def due_days(self, val: int) -> None:
        self._due_days = val


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
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=True)
    variant = Column(JSON, nullable=False, default=dict)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_id = Column(Uuid(as_uuid=True), ForeignKey("taxes.id"), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    _description = Column("description", String(255), nullable=True)

    subscription = relationship("Subscription", back_populates="lines", lazy="select")
    product = relationship("Product", lazy="select")
    tax = relationship("Tax", lazy="select")

    @property
    def description(self) -> str:
        if self._description is not None:
            return self._description
        return self.product.name if self.product else "Product"

    @description.setter
    def description(self, val: str) -> None:
        self._description = val


class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)
    changed_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=now)
    note = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True, default=dict)

    subscription = relationship("Subscription", back_populates="history", lazy="select")
    changed_by_user = relationship("User", lazy="select")

    @property
    def user(self):
        return self.changed_by_user
