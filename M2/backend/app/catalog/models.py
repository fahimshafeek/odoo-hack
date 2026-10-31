import uuid
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Integer,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.clock import now


class Tax(Base):
    __tablename__ = "taxes"
    __table_args__ = (
        CheckConstraint("rate_percent >= 0 AND rate_percent <= 100", name="ck_taxes_rate_percent_range"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), unique=True, nullable=False, index=True)
    rate_percent = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("sales_price >= 0", name="ck_products_sales_price_non_negative"),
        CheckConstraint("cost_price >= 0", name="ck_products_cost_price_non_negative"),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_name", "name"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    type = Column(String(40), nullable=False, default="physical")
    sales_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    cost_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    notes = Column(String(2000), nullable=True)
    tax_id = Column(Uuid(as_uuid=True), ForeignKey("taxes.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    tax = relationship("Tax", lazy="raise")
    attributes = relationship(
        "ProductAttribute",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductAttribute.name",
        lazy="raise",
    )


class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_product_attributes_product_name"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(80), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    product = relationship("Product", back_populates="attributes", lazy="raise")
    values = relationship(
        "AttributeValue",
        back_populates="attribute",
        cascade="all, delete-orphan",
        order_by="AttributeValue.name",
        lazy="raise",
    )


class AttributeValue(Base):
    __tablename__ = "attribute_values"
    __table_args__ = (
        UniqueConstraint("attribute_id", "name", name="uq_attribute_values_attr_name"),
        CheckConstraint("extra_price >= 0", name="ck_attribute_values_extra_price_non_negative"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribute_id = Column(Uuid(as_uuid=True), ForeignKey("product_attributes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(80), nullable=False)
    extra_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    attribute = relationship("ProductAttribute", back_populates="values", lazy="raise")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_plans_price_non_negative"),
        CheckConstraint("min_quantity >= 1", name="ck_plans_min_quantity_ge_1"),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_plans_valid_dates_order",
        ),
        CheckConstraint(
            "billing_period IN ('daily', 'weekly', 'monthly', 'yearly')",
            name="ck_plans_billing_period_enum",
        ),
        Index("ix_plans_is_active", "is_active"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    billing_period = Column(String(20), nullable=False, default="monthly")
    min_quantity = Column(Integer, nullable=False, default=1)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    tax_id = Column(Uuid(as_uuid=True), ForeignKey("taxes.id"), nullable=True)
    auto_close = Column(Boolean, nullable=False, default=False)
    allow_early_close = Column(Boolean, nullable=False, default=True)
    allow_pause = Column(Boolean, nullable=False, default=True)
    allow_renew = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    tax = relationship("Tax", lazy="raise")


class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    __table_args__ = (
        CheckConstraint("due_days >= 0 AND due_days <= 365", name="ck_payment_terms_due_days_range"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(60), unique=True, nullable=False, index=True)
    due_days = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"
    __table_args__ = (
        CheckConstraint("validity_days >= 1 AND validity_days <= 365", name="ck_quotation_templates_validity_days"),
        Index("ix_quotation_templates_is_active", "is_active"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    plan_id = Column(Uuid(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    validity_days = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    plan = relationship("Plan", lazy="raise")
    lines = relationship(
        "TemplateLine",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateLine.position",
        lazy="raise",
    )


class TemplateLine(Base):
    __tablename__ = "template_lines"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_template_lines_quantity_ge_1"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(Uuid(as_uuid=True), ForeignKey("quotation_templates.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant = Column(JSON, nullable=False, default=dict)  # {"value_ids": [uuid, ...]}
    quantity = Column(Integer, nullable=False, default=1)
    position = Column(Integer, nullable=False, default=0)
    tax_id = Column(Uuid(as_uuid=True), ForeignKey("taxes.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    template = relationship("QuotationTemplate", back_populates="lines", lazy="raise")
    product = relationship("Product", lazy="raise")
    tax = relationship("Tax", lazy="raise")
