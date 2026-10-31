from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    customer_id: str | None = None
    is_active: bool

class AuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=9, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=120)
    company_name: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)

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
    full_name: str | None = Field(None, max_length=120)
    is_active: bool | None = None

class CustomerCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)
    company_name: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)
    billing_address: str | None = Field(None, max_length=500)
    tax_id: str | None = Field(None, max_length=50)

class CustomerUpdateRequest(BaseModel):
    company_name: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)
    billing_address: str | None = Field(None, max_length=500)
    tax_id: str | None = Field(None, max_length=50)

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None = None
    email: str | None = None
    full_name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    billing_address: str | None = None
    tax_id: str | None = None
    created_at: datetime
