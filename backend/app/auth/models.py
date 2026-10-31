import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.types import Uuid
from sqlalchemy.orm import relationship
from app.core.clock import now
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # admin, staff, customer
    full_name = Column(String(120), nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    customer_profile = relationship("Customer", back_populates="user", uselist=False, lazy="select")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    @property
    def customer(self):
        """Compatibility property for M2."""
        return self.customer_profile

    @customer.setter
    def customer(self, val):
        self.customer_profile = val


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True)
    company_name = Column(String(120), nullable=True, default="")
    phone = Column(String(30), nullable=True, default="")
    billing_address = Column(Text, nullable=True, default="")
    tax_id = Column(String(50), nullable=True, default="")

    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    user = relationship("User", back_populates="customer_profile", lazy="select")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=now)

    user = relationship("User", back_populates="password_reset_tokens")
