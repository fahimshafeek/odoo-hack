import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship
from app.core.clock import now
from app.core.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # admin, staff, customer
    full_name = Column(String(120), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    customer_profile = relationship("Customer", back_populates="user", uselist=False)
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=True)
    company_name = Column(String(120), nullable=True)
    phone = Column(String(30), nullable=True)
    billing_address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)

    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    user = relationship("User", back_populates="customer_profile")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now)

    user = relationship("User", back_populates="password_reset_tokens")
