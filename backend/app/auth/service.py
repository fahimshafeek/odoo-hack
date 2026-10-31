import secrets
import uuid
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
    """Registers a new account (AUTH-1, AUTH-2) with role support."""
    norm_email = data.email.strip().lower()

    # Password complexity check (AUTH-2)
    validate_password_or_raise(data.password, norm_email)

    # Email uniqueness check
    existing = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing:
        raise AppError(code="email_taken", message="An account with this email already exists.", status_code=409)

    user_role = data.role if data.role in ("customer", "staff", "admin") else "customer"
    user = User(
        email=norm_email,
        password_hash=hash_password(data.password),
        role=user_role,
        full_name=data.full_name.strip(),
        is_active=True,
    )
    session.add(user)
    session.flush()

    customer = None
    if user_role == "customer":
        customer = Customer(
            user_id=user.id,
            company_name=data.company_name.strip() if data.company_name else None,
            phone=data.phone.strip() if data.phone else None,
        )
        session.add(customer)
        session.flush()

    customer_id = str(customer.id) if customer else None
    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        customer_id=customer_id,
        full_name=user.full_name,
        email=user.email,
    )
    return user, token


def authenticate_user(session: Session, email: str, password: str) -> tuple[User, str]:
    """Validates credentials and returns User plus JWT access token."""
    norm_email = email.strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == norm_email))

    if not user or not verify_password(password, user.password_hash):
        raise AppError(code="invalid_credentials", message="Invalid email or password.", status_code=401)

    if not user.is_active:
        raise AppError(code="account_inactive", message="Your account is deactivated.", status_code=403)

    customer_id = str(user.customer_profile.id) if user.customer_profile else None
    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        customer_id=customer_id,
        full_name=user.full_name,
        email=user.email,
    )
    return user, token


def initiate_password_reset(session: Session, email: str) -> None:
    """Creates a 5-minute single-use token and dispatches reset email."""
    norm_email = email.strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == norm_email))

    if not user or not user.is_active:
        return

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None,
    )
    session.add(prt)
    session.flush()

    reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    send_password_reset_email(user.email, reset_url, settings.PASSWORD_RESET_EXPIRE_MINUTES)


def complete_password_reset(session: Session, raw_token: str, new_password: str) -> None:
    """Verifies token validity and updates user password."""
    token_hash = hash_token(raw_token)
    prt = session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )

    curr_now = now()
    exp_at = prt.expires_at
    if exp_at.tzinfo is None:
        exp_at = exp_at.replace(tzinfo=curr_now.tzinfo)

    if not prt or prt.used_at is not None or exp_at < curr_now:
        raise AppError(
            code="invalid_or_expired_token",
            message="Password reset link is invalid or has expired.",
            status_code=400,
        )

    user = session.get(User, prt.user_id)
    if not user or not user.is_active:
        raise AppError(code="account_inactive", message="User account not found or inactive.", status_code=400)

    validate_password_or_raise(new_password, user.email)

    user.password_hash = hash_password(new_password)
    prt.used_at = now()
    session.flush()


def create_staff_member(session: Session, data: StaffCreateRequest) -> User:
    """Creates staff user with randomized initial password and sends invite."""
    norm_email = data.email.strip().lower()
    existing = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing:
        raise AppError(code="email_taken", message="An account with this email already exists.", status_code=409)

    random_temp_pass = secrets.token_urlsafe(24)
    user = User(
        email=norm_email,
        password_hash=hash_password(random_temp_pass),
        role="staff",
        full_name=data.full_name.strip(),
        is_active=True,
    )
    session.add(user)
    session.flush()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now() + timedelta(hours=24),
    )
    session.add(prt)
    session.flush()

    invite_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    send_staff_invite_email(user.email, invite_url, user.full_name)

    return user


def list_staff_members(session: Session, params: PageParams):
    stmt = select(User).where(User.role.in_(["admin", "staff"]))
    if params.q:
        q_wildcard = f"%{params.q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(User.email).like(q_wildcard),
                func.lower(User.full_name).like(q_wildcard),
            )
        )
    allowed_sort = {
        "email": User.email,
        "full_name": User.full_name,
        "role": User.role,
        "created_at": User.created_at,
        "is_active": User.is_active,
    }
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort=User.created_at.desc())


def update_staff_member(session: Session, staff_id: uuid.UUID | str, data: StaffUpdateRequest) -> User:
    try:
        u_id = uuid.UUID(str(staff_id))
    except (ValueError, TypeError):
        raise AppError(code="not_found", message="Staff member not found.", status_code=404)

    user = session.get(User, u_id)
    if not user or user.role not in ["staff", "admin"]:
        raise AppError(code="not_found", message="Staff member not found.", status_code=404)

    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.is_active is not None:
        user.is_active = data.is_active

    session.flush()
    return user


def create_customer_record(session: Session, data: CustomerCreateRequest) -> Customer:
    norm_email = data.email.strip().lower()
    existing_user = session.scalar(select(User).where(func.lower(User.email) == norm_email))
    if existing_user:
        raise AppError(code="email_taken", message="An account with this email already exists.", status_code=409)

    user = User(
        email=norm_email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
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
    return customer


# Compatibility aliases for router
create_customer_by_admin = create_customer_record
create_staff_user = create_staff_member
list_staff_users = list_staff_members
update_staff_user = update_staff_member
request_password_reset = initiate_password_reset
reset_password_with_token = complete_password_reset



def list_customers(session: Session, params: PageParams):
    stmt = select(Customer).join(User, Customer.user_id == User.id)
    if params.q:
        q_wildcard = f"%{params.q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(User.email).like(q_wildcard),
                func.lower(User.full_name).like(q_wildcard),
                func.lower(Customer.company_name).like(q_wildcard),
                Customer.phone.like(q_wildcard),
            )
        )
    allowed_sort = {
        "email": User.email,
        "full_name": User.full_name,
        "company_name": Customer.company_name,
        "created_at": Customer.created_at,
    }
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort=Customer.created_at.desc())


def get_customer_by_id(session: Session, customer_id: uuid.UUID | str) -> Customer:
    try:
        c_id = uuid.UUID(str(customer_id))
    except (ValueError, TypeError):
        raise AppError(code="not_found", message="Customer not found.", status_code=404)

    customer = session.get(Customer, c_id)
    if not customer:
        raise AppError(code="not_found", message="Customer not found.", status_code=404)
    return customer


def update_customer_profile(session: Session, customer_id: uuid.UUID | str, data: CustomerUpdateRequest) -> Customer:
    customer = get_customer_by_id(session, customer_id)
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


# Compatibility aliases for router
create_customer_by_admin = create_customer_record
create_staff_user = create_staff_member
list_staff_users = list_staff_members
update_staff_user = update_staff_member
request_password_reset = initiate_password_reset
reset_password_with_token = complete_password_reset

