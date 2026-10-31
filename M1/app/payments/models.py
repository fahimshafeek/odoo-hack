import uuid
from decimal import Decimal
from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.core.clock import now
from app.core.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    method = Column(String(30), nullable=False, default="bank_transfer")
    amount = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    paid_on = Column(Date, nullable=False, index=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now)

    invoice = relationship("app.billing.models.Invoice", back_populates="payments")
    customer = relationship("app.auth.models.Customer")
