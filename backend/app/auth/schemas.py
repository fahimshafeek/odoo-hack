import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | str
    email: str
    full_name: str
    role: str
    customer_id: uuid.UUID | str | None = None
    is_active: bool


class AuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=9, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=120)
    company_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=9, max_length=128)


class StaffCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)


class StaffUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = None


class CustomerCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)
    company_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    billing_address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)


class CustomerUpdateRequest(BaseModel):
    company_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    billing_address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | str
    email: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
