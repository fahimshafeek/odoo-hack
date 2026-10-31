import uuid
from decimal import Decimal
from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, String, Text
from app.core.clock import now
from app.core.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    type = Column(String(50), nullable=False, default="service")
    sales_price = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    cost_price = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=now)

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    price = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    billing_period = Column(String(20), nullable=False, default="monthly")  # daily, weekly, monthly, yearly
    min_quantity = Column(Numeric(10, 0), nullable=False, default=1)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    auto_close = Column(Boolean, nullable=False, default=False)
    allow_early_close = Column(Boolean, nullable=False, default=True)
    allow_pause = Column(Boolean, nullable=False, default=True)
    allow_renew = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=now)
