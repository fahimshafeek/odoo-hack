import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.clock import now


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # admin | staff | customer
    full_name = Column(String(120), nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    customer = relationship("Customer", back_populates="user", uselist=False, lazy="select")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, unique=True)
    company_name = Column(String(120), nullable=False, default="")
    phone = Column(String(20), nullable=False, default="")
    billing_address = Column(String(500), nullable=False, default="")
    tax_id = Column(String(50), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    user = relationship("User", back_populates="customer", lazy="select")
