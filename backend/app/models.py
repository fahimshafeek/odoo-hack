"""Compatibility proxy re-exporting all ORM models for unified access."""
from app.auth.models import User, Customer, PasswordResetToken
from app.catalog.models import (
    Tax,
    Product,
    ProductAttribute,
    AttributeValue,
    Plan,
    PaymentTerm,
    QuotationTemplate,
    TemplateLine,
)
from app.subscriptions.models import Subscription, SubscriptionLine, SubscriptionHistory
from app.billing.models import (
    Discount,
    DiscountTarget,
    DiscountRedemption,
    Invoice,
    InvoiceLine,
    BillingRun,
)
from app.payments.models import Payment
from app.core.numbering import DocumentSequence, next_number

SubscriptionStub = Subscription
SubscriptionLineStub = SubscriptionLine
