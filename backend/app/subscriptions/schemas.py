import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.core.money import Money
from app.catalog.schemas import CustomerRef, PlanRef, ProductRef, TaxRef, UserRef


class PaymentTermRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    due_days: int


class SubscriptionLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    variant_value_ids: List[uuid.UUID] = Field(default_factory=list)
    tax_id: Optional[uuid.UUID] = None


class SubscriptionLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product: ProductRef
    variant: dict  # {"selections": [{"attribute": ..., "value": ..., "extra_price": ...}]}
    quantity: int
    unit_price: Money
    tax: Optional[TaxRef] = None
    tax_rate: Money
    amount: Money
    tax_amount: Money
    total: Money


class PlanFeeLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    amount: Money
    tax_rate: Money
    tax_amount: Money
    total: Money


class TotalsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    subtotal: Money
    tax_total: Money
    total: Money


class SubscriptionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: str
    status: str
    customer: CustomerRef
    plan: PlanRef
    start_date: datetime.date
    expiry_date: datetime.date
    next_billing_date: Optional[datetime.date] = None
    estimated_total: Money
    allowed_actions: List[str] = Field(default_factory=list)


class SubscriptionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: str
    status: str
    customer: CustomerRef
    plan: PlanRef
    start_date: datetime.date
    expiry_date: datetime.date
    next_billing_date: Optional[datetime.date] = None
    estimated_total: Money
    allowed_actions: List[str] = Field(default_factory=list)
    payment_term: PaymentTermRef
    quote_valid_until: Optional[datetime.date] = None
    template_id: Optional[uuid.UUID] = None
    can_edit: bool
    lines: List[SubscriptionLineOut] = Field(default_factory=list)
    plan_fee: Optional[PlanFeeLine] = None
    totals: TotalsOut
    created_at: datetime.datetime


class SubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    start_date: datetime.date
    expiry_date: datetime.date
    payment_term_id: uuid.UUID
    lines: List[SubscriptionLineInput] = Field(default_factory=list)


class SubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: Optional[datetime.date] = None
    expiry_date: Optional[datetime.date] = None
    payment_term_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    lines: Optional[List[SubscriptionLineInput]] = None


class FromTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: uuid.UUID
    start_date: Optional[datetime.date] = None
    expiry_date: Optional[datetime.date] = None
    payment_term_id: Optional[uuid.UUID] = None


class TransitionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    note: Optional[str] = None


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    from_status: str
    to_status: str
    action: str
    changed_by: Optional[UserRef] = None
    changed_at: datetime.datetime
    note: Optional[str] = None


# --- Price Preview Schemas ---

class PricePreviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: Optional[uuid.UUID] = None
    lines: List[SubscriptionLineInput] = Field(default_factory=list)


class PricePreviewLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: uuid.UUID
    unit_price: Money
    amount: Money
    tax_rate: Money
    tax_amount: Money
    total: Money


class PricePreviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    lines: List[PricePreviewLine]
    plan_fee: Optional[PlanFeeLine] = None
    totals: TotalsOut
