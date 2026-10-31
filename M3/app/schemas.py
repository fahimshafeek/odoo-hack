"""
Pydantic v2 schemas for M3: Billing & Payments.
Strict validation and formatting.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core_compat import Money


class SchemaBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        from_attributes=True,
    )


# -----------------------------------------------------------------------------
# References
# -----------------------------------------------------------------------------
class CustomerRef(SchemaBase):
    id: uuid.UUID
    name: str
    email: str


class PlanRef(SchemaBase):
    id: uuid.UUID
    name: str
    billing_period: str


class ProductRef(SchemaBase):
    id: uuid.UUID
    name: str


class TaxRef(SchemaBase):
    id: uuid.UUID
    name: str
    rate_percent: Money


class UserRef(SchemaBase):
    id: uuid.UUID
    name: str


class SubscriptionRef(SchemaBase):
    id: uuid.UUID
    number: str


# -----------------------------------------------------------------------------
# Tax Schemas
# -----------------------------------------------------------------------------
class TaxCreate(SchemaBase):
    name: str = Field(min_length=1, max_length=60)
    rate_percent: Money
    is_active: bool = True

    @field_validator("rate_percent")
    @classmethod
    def validate_rate(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00") or v > Decimal("100.00"):
            raise ValueError("rate_percent must be between 0.00 and 100.00")
        return v


class TaxUpdate(SchemaBase):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    rate_percent: Money | None = None
    is_active: bool | None = None

    @field_validator("rate_percent")
    @classmethod
    def validate_rate(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v < Decimal("0.00") or v > Decimal("100.00")):
            raise ValueError("rate_percent must be between 0.00 and 100.00")
        return v


class TaxOut(SchemaBase):
    id: uuid.UUID
    name: str
    rate_percent: Money
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# Discount Schemas
# -----------------------------------------------------------------------------
class DiscountTargetInput(SchemaBase):
    product_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_exclusive(self) -> DiscountTargetInput:
        if (self.product_id is None and self.subscription_id is None) or (
            self.product_id is not None and self.subscription_id is not None
        ):
            raise ValueError(
                "Exactly one of product_id or subscription_id must be provided"
            )
        return self


class DiscountTargetOut(SchemaBase):
    product_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    label: str = ""


class DiscountCreate(SchemaBase):
    name: str = Field(min_length=1, max_length=120)
    type: Literal["fixed", "percent"]
    value: Money
    scope: Literal["product", "subscription"]
    min_purchase: Money | None = None
    min_quantity: int | None = Field(default=None, ge=1)
    start_date: date
    end_date: date
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool = True
    targets: list[DiscountTargetInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rules(self) -> DiscountCreate:
        if self.type == "percent" and self.value > Decimal("100.00"):
            raise ValueError("Percent discount value cannot exceed 100.00%")
        if self.value <= Decimal("0.00"):
            raise ValueError("Discount value must be greater than 0")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        if self.min_purchase is not None and self.min_purchase < Decimal("0.00"):
            raise ValueError("min_purchase must be non-negative")
        for t in self.targets:
            if self.scope == "product" and t.product_id is None:
                raise ValueError("Product scope discount can only target products")
            if self.scope == "subscription" and t.subscription_id is None:
                raise ValueError(
                    "Subscription scope discount can only target subscriptions"
                )
        return self


class DiscountUpdate(SchemaBase):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: Literal["fixed", "percent"] | None = None
    value: Money | None = None
    scope: Literal["product", "subscription"] | None = None
    min_purchase: Money | None = None
    min_quantity: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    targets: list[DiscountTargetInput] | None = None


class DiscountOut(SchemaBase):
    id: uuid.UUID
    name: str
    type: str
    value: Money
    scope: str
    min_purchase: Money | None
    min_quantity: int | None
    start_date: date
    end_date: date
    usage_limit: int | None
    used_count: int
    is_active: bool
    targets: list[DiscountTargetOut]
    editable_fields: list[str]


# -----------------------------------------------------------------------------
# Payment Schemas
# -----------------------------------------------------------------------------
class PaymentCreate(SchemaBase):
    method: Literal["cash", "bank_transfer", "card", "upi", "cheque", "online"]
    amount: Money
    paid_on: date | None = None
    note: str | None = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0.00"):
            raise ValueError("Payment amount must be greater than 0")
        return v


class MockPayInput(SchemaBase):
    amount: Money | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0.00"):
            raise ValueError("Payment amount must be greater than 0")
        return v


class PaymentOut(SchemaBase):
    id: uuid.UUID
    invoice_id: uuid.UUID
    customer_id: uuid.UUID
    method: str
    amount: Money
    paid_on: date
    note: str | None
    recorded_by: uuid.UUID | None
    created_at: datetime


# -----------------------------------------------------------------------------
# Invoice Schemas
# -----------------------------------------------------------------------------
class InvoiceLineOut(SchemaBase):
    id: uuid.UUID
    line_type: str
    description: str
    product_id: uuid.UUID | None
    quantity: int
    unit_price: Money
    gross_amount: Money
    discount_amount: Money
    discount: dict[str, Any] | None = None
    tax_rate: Money
    tax_amount: Money
    line_total: Money
    position: int


class InvoiceListItem(SchemaBase):
    id: uuid.UUID
    number: str
    status: str
    payment_state: str
    is_overdue: bool
    days_overdue: int
    customer: CustomerRef
    subscription: SubscriptionRef
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    total: Money
    amount_paid: Money
    balance: Money


class InvoiceDetail(InvoiceListItem):
    subtotal: Money
    discount_total: Money
    tax_total: Money
    confirmed_at: datetime | None
    sent_at: datetime | None
    cancelled_at: datetime | None
    customer_billing: dict[str, Any] | None = None
    lines: list[InvoiceLineOut]
    payments: list[PaymentOut] = Field(default_factory=list)
    allowed_actions: list[str]


# -----------------------------------------------------------------------------
# Billing Run Schemas
# -----------------------------------------------------------------------------
class BillingRunTriggerInput(SchemaBase):
    as_of: date | None = None


class BillingRunOut(SchemaBase):
    id: uuid.UUID
    run_date: date
    status: str
    started_at: datetime
    finished_at: datetime | None
    total_due: int
    processed: int
    created_count: int
    skipped_count: int
    failed_count: int
    error: str | None
    triggered_by: UserRef | None = None
