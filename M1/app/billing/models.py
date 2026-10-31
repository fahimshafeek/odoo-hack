import uuid
from decimal import Decimal
from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.clock import now
from app.core.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number = Column(String(30), unique=True, index=True, nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)

    subtotal = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    discount_total = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    tax_total = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    total = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))
    amount_paid = Column(Numeric(12, 2, asdecimal=True), nullable=False, default=Decimal("0.00"))

    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", name="uq_invoice_sub_period"),
    )

    customer = relationship("app.auth.models.Customer")
    subscription = relationship("app.subscriptions.models.Subscription")
    payments = relationship("app.payments.models.Payment", back_populates="invoice")
