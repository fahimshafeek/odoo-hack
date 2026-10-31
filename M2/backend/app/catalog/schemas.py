import uuid
import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.money import Money


class TaxRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    rate_percent: Money


class ProductRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class PlanRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    billing_period: str


class CustomerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    email: str


class UserRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


# --- Product Attribute Schemas ---

class AttributeValueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=80)
    extra_price: Money = Field(default=Money("0.00"))


class AttributeValueUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[uuid.UUID] = None
    name: str = Field(..., max_length=80)
    extra_price: Money = Field(default=Money("0.00"))


class AttributeValueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    extra_price: Money


class ProductAttributeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=80)
    values: List[AttributeValueCreate] = Field(default_factory=list)


class ProductAttributeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., max_length=80)
    values: List[AttributeValueUpdate] = Field(default_factory=list)


class ProductAttributeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    values: List[AttributeValueOut] = Field(default_factory=list)


# --- Product Schemas ---

class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=120)
    type: str = Field(default="physical", max_length=40)
    sales_price: Money = Field(..., description="Sales price <= 9,999,999.99")
    cost_price: Money = Field(..., description="Cost price <= 9,999,999.99")
    notes: Optional[str] = Field(default=None, max_length=2000)
    tax_id: Optional[uuid.UUID] = None
    is_active: bool = True

    @field_validator("name", "type")
    @classmethod
    def strip_text(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("String cannot be empty or whitespace only")
        return s


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    type: Optional[str] = Field(default=None, max_length=40)
    sales_price: Optional[Money] = None
    cost_price: Optional[Money] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    tax_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    type: str
    sales_price: Money
    cost_price: Money
    tax: Optional[TaxRef] = None
    is_active: bool


class ProductDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    type: str
    sales_price: Money
    cost_price: Money
    notes: Optional[str] = None
    tax_id: Optional[uuid.UUID] = None
    tax: Optional[TaxRef] = None
    is_active: bool
    attributes: List[ProductAttributeOut] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# --- Plan Schemas ---

BillingPeriodEnum = Literal["daily", "weekly", "monthly", "yearly"]


class PlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=120)
    price: Money
    billing_period: BillingPeriodEnum
    min_quantity: int = Field(default=1, ge=1)
    valid_from: Optional[datetime.date] = None
    valid_to: Optional[datetime.date] = None
    tax_id: Optional[uuid.UUID] = None
    auto_close: bool = False
    allow_early_close: bool = True
    allow_pause: bool = True
    allow_renew: bool = True
    is_active: bool = True


class PlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    price: Optional[Money] = None
    billing_period: Optional[BillingPeriodEnum] = None
    min_quantity: Optional[int] = Field(default=None, ge=1)
    valid_from: Optional[datetime.date] = None
    valid_to: Optional[datetime.date] = None
    tax_id: Optional[uuid.UUID] = None
    auto_close: Optional[bool] = None
    allow_early_close: Optional[bool] = None
    allow_pause: Optional[bool] = None
    allow_renew: Optional[bool] = None
    is_active: Optional[bool] = None


class PlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    price: Money
    billing_period: str
    min_quantity: int
    valid_from: Optional[datetime.date] = None
    valid_to: Optional[datetime.date] = None
    tax: Optional[TaxRef] = None
    tax_id: Optional[uuid.UUID] = None
    auto_close: bool
    allow_early_close: bool
    allow_pause: bool
    allow_renew: bool
    is_active: bool


# --- Payment Term Schemas ---

class PaymentTermCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=60)
    due_days: int = Field(default=0, ge=0, le=365)


class PaymentTermUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    due_days: Optional[int] = Field(default=None, ge=0, le=365)
    is_active: Optional[bool] = None


class PaymentTermOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    due_days: int
    is_active: bool


# --- Quotation Template Schemas ---

class TemplateLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    variant_value_ids: List[uuid.UUID] = Field(default_factory=list)
    tax_id: Optional[uuid.UUID] = None


class TemplateLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product: ProductRef
    variant: dict
    quantity: int
    unit_price: Money
    tax: Optional[TaxRef] = None
    tax_rate: Money
    amount: Money
    position: int


class QuotationTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=120)
    plan_id: uuid.UUID
    validity_days: int = Field(default=30, ge=1, le=365)
    lines: List[TemplateLineInput] = Field(default_factory=list)


class QuotationTemplateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    plan_id: Optional[uuid.UUID] = None
    validity_days: Optional[int] = Field(default=None, ge=1, le=365)
    lines: Optional[List[TemplateLineInput]] = None
    is_active: Optional[bool] = None


class QuotationTemplateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    plan: PlanRef
    validity_days: int
    is_active: bool
    lines_count: int


class QuotationTemplateDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    plan: PlanRef
    plan_id: uuid.UUID
    validity_days: int
    is_active: bool
    lines: List[TemplateLineOut] = Field(default_factory=list)
