import uuid
from decimal import Decimal
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.core.clock import now
from app.core.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number = Column(String(30), unique=True, index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    next_billing_date = Column(Date, nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=now)

    customer = relationship("app.auth.models.Customer")
    plan = relationship("app.catalog.models.Plan")
    lines = relationship("SubscriptionLine", back_populates="subscription")

class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    amount = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("app.catalog.models.Product")
