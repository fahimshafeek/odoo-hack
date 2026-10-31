import secrets
from datetime import timedelta
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.auth.models import Customer, PasswordResetToken, User
from app.auth.schemas import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    SignupRequest,
    StaffCreateRequest,
    StaffUpdateRequest,
)
from app.auth.validators import validate_password_or_raise
from app.core.clock import now
from app.core.config import settings
from app.core.errors import AppError
from app.core.mail import send_password_reset_email, send_staff_invite_email
from app.core.pagination import PageParams, paginate
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    verify_password,
)

def signup_customer(session: Session, data: SignupRequest) -> tuple[User, str]:
    """Registers a new customer account (AUTH-1, AUTH-2)."""
    norm_email = data.email.strip().lower()

    # Password complexity check (AUTH-2)
    validate_password_or_raise(data.password, norm_email)

    # Email uniqueness check
    existing = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing:
        raise AppError(code="email_taken", message="An account with this email already exists.", status_code=409)

    user = User(
        email=norm_email,
        password_hash=hash_password(data.password),
        role="customer",
        full_name=data.full_name.strip(),
        is_active=True,
    )
    session.add(user)
    session.flush()

    customer = Customer(
        user_id=user.id,
        company_name=data.company_name.strip() if data.company_name else None,
        phone=data.phone.strip() if data.phone else None,
    )
    session.add(customer)
    session.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        customer_id=customer.id,
        full_name=user.full_name,
    )
    return user, token

def authenticate_user(session: Session, email: str, password: str) -> tuple[User, str]:
    """Authenticates a user and returns their JWT token."""
    norm_email = email.strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == norm_email))

    if not user or not verify_password(password, user.password_hash):
        raise AppError(code="unauthorized", message="Invalid email or password", status_code=401)

    if not user.is_active:
        raise AppError(code="unauthorized", message="This account has been deactivated", status_code=401)

    customer_id = user.customer_profile.id if user.customer_profile else None
    token = create_access_token(
        user_id=user.id,
        role=user.role,
        customer_id=customer_id,
        full_name=user.full_name,
    )
    return user, token

def request_password_reset(session: Session, email: str) -> None:
    """Generates a 5-minute single-use token and sends an email via Resend (AUTH-3)."""
    norm_email = email.strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == norm_email))

    # Anti-enumeration: always succeed silently even if email is unknown
    if not user or not user.is_active:
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash_val = hash_token(raw_token)
    expires_at = now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash_val,
        expires_at=expires_at,
    )
    session.add(reset_token)
    session.flush()

    reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    send_password_reset_email(
        to_email=user.email,
        reset_url=reset_url,
        expires_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )

def reset_password_with_token(session: Session, token: str, new_password: str) -> None:
    """Validates the reset token and updates the password."""
    token_hash_val = hash_token(token.strip())
    reset_record = session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash_val,
            PasswordResetToken.used_at.is_(None)
        )
    )

    if not reset_record:
        raise AppError(code="invalid_token", message="Invalid or already used reset token", status_code=400)

    exp = reset_record.expires_at.replace(tzinfo=None) if reset_record.expires_at.tzinfo else reset_record.expires_at
    curr = now().replace(tzinfo=None) if now().tzinfo else now()
    if curr > exp:
        raise AppError(code="token_expired", message="Reset link has expired (valid for 5 minutes)", status_code=400)

    user = session.scalar(select(User).where(User.id == reset_record.user_id))
    if not user or not user.is_active:
        raise AppError(code="not_found", message="User not found or inactive", status_code=404)

    validate_password_or_raise(new_password, user.email)

    user.password_hash = hash_password(new_password)
    reset_record.used_at = now()
    session.flush()

def create_staff_user(session: Session, data: StaffCreateRequest) -> User:
    """Admin-only staff creation. Sends 24-hr setup invite email via Resend (AUTH-5)."""
    norm_email = data.email.strip().lower()

    existing = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing:
        raise AppError(code="email_taken", message="An account with this email already exists", status_code=409)

    random_pw = secrets.token_urlsafe(24)
    staff_user = User(
        email=norm_email,
        password_hash=hash_password(random_pw),
        role="staff",
        full_name=data.full_name.strip(),
        is_active=True,
    )
    session.add(staff_user)
    session.flush()

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=staff_user.id,
        token_hash=hash_token(raw_token),
        expires_at=now() + timedelta(hours=24),
    )
    session.add(reset_token)
    session.flush()

    invite_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}&invite=1"
    send_staff_invite_email(to_email=staff_user.email, invite_url=invite_url, full_name=staff_user.full_name)

    return staff_user

def list_staff_users(session: Session, params: PageParams) -> tuple[list[User], int]:
    stmt = select(User).where(User.role == "staff")
    if params.q:
        search = f"%{params.q}%"
        stmt = stmt.where(or_(User.email.ilike(search), User.full_name.ilike(search)))

    allowed_sort = {"created_at": User.created_at, "full_name": User.full_name, "email": User.email}
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort=User.created_at.desc())

def update_staff_user(session: Session, staff_id: str, data: StaffUpdateRequest) -> User:
    staff_user = session.scalar(select(User).where(User.id == staff_id, User.role == "staff"))
    if not staff_user:
        raise AppError(code="not_found", message="Staff user not found", status_code=404)

    if data.full_name is not None:
        staff_user.full_name = data.full_name.strip()
    if data.is_active is not None:
        staff_user.is_active = data.is_active

    session.flush()
    return staff_user

def create_customer_by_admin(session: Session, data: CustomerCreateRequest) -> Customer:
    """Admin/Staff creates customer with automated invite email."""
    norm_email = data.email.strip().lower()

    existing = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing:
        raise AppError(code="email_taken", message="An account with this email already exists", status_code=409)

    random_pw = secrets.token_urlsafe(24)
    user = User(
        email=norm_email,
        password_hash=hash_password(random_pw),
        role="customer",
        full_name=data.full_name.strip(),
        is_active=True,
    )
    session.add(user)
    session.flush()

    customer = Customer(
        user_id=user.id,
        company_name=data.company_name.strip() if data.company_name else None,
        phone=data.phone.strip() if data.phone else None,
        billing_address=data.billing_address.strip() if data.billing_address else None,
        tax_id=data.tax_id.strip() if data.tax_id else None,
    )
    session.add(customer)
    session.flush()

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now() + timedelta(hours=24),
    )
    session.add(reset_token)
    session.flush()

    invite_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}&invite=1"
    send_staff_invite_email(to_email=user.email, invite_url=invite_url, full_name=user.full_name)

    return customer

def list_customers(session: Session, params: PageParams) -> tuple[list[Customer], int]:
    stmt = select(Customer).join(User, Customer.user_id == User.id, isouter=True)
    if params.q:
        search = f"%{params.q}%"
        stmt = stmt.where(
            or_(
                Customer.company_name.ilike(search),
                Customer.phone.ilike(search),
                User.full_name.ilike(search),
                User.email.ilike(search),
            )
        )

    allowed_sort = {"created_at": Customer.created_at, "company_name": Customer.company_name}
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort=Customer.created_at.desc())

def update_customer_profile(session: Session, customer_id: str, data: CustomerUpdateRequest) -> Customer:
    customer = session.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise AppError(code="not_found", message="Customer profile not found", status_code=404)

    if data.company_name is not None:
        customer.company_name = data.company_name.strip()
    if data.phone is not None:
        customer.phone = data.phone.strip()
    if data.billing_address is not None:
        customer.billing_address = data.billing_address.strip()
    if data.tax_id is not None:
        customer.tax_id = data.tax_id.strip()

    session.flush()
    return customer
