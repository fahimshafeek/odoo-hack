from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.models import Customer
from app.auth.ratelimit import check_login_rate_limit, clear_login_attempts, record_failed_login
from app.auth.schemas import (
    AuthSession,
    CustomerCreateRequest,
    CustomerOut,
    CustomerUpdateRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    StaffCreateRequest,
    StaffUpdateRequest,
    UserOut,
)
from app.auth.service import (
    authenticate_user,
    create_customer_by_admin,
    create_staff_user,
    list_customers,
    list_staff_users,
    request_password_reset,
    reset_password_with_token,
    signup_customer,
    update_customer_profile,
    update_staff_user,
)
from app.core.db import get_session
from app.core.deps import AuthUser, CurrentUser, require_role
from app.core.errors import AppError
from app.core.pagination import Page, PageParams

router = APIRouter(tags=["auth"])
portal_router = APIRouter(tags=["portal_auth"])

def _to_user_out(user) -> UserOut:
    cid = user.customer_profile.id if user.customer_profile else None
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        customer_id=cid,
        is_active=user.is_active,
    )

def _to_customer_out(cust: Customer) -> CustomerOut:
    return CustomerOut(
        id=cust.id,
        user_id=cust.user_id,
        email=cust.user.email if cust.user else None,
        full_name=cust.user.full_name if cust.user else None,
        company_name=cust.company_name,
        phone=cust.phone,
        billing_address=cust.billing_address,
        tax_id=cust.tax_id,
        created_at=cust.created_at,
    )

# ----------------- PUBLIC AUTH ROUTES -----------------

@router.post("/auth/signup", response_model=AuthSession, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    """Customer registration with live password validation (AUTH-1, AUTH-2)."""
    user, token = signup_customer(session, data)
    session.commit()
    return AuthSession(access_token=token, user=_to_user_out(user))

@router.post("/auth/login", response_model=AuthSession)
def login(request: Request, data: LoginRequest, session: Session = Depends(get_session)):
    """User authentication with rate limiting (AUTH-4)."""
    check_login_rate_limit(request, data.email)
    try:
        user, token = authenticate_user(session, data.email, data.password)
        clear_login_attempts(request, data.email)
        return AuthSession(access_token=token, user=_to_user_out(user))
    except AppError:
        record_failed_login(request, data.email)
        raise

@router.get("/auth/me", response_model=UserOut)
def get_me(current_user: CurrentUser, session: Session = Depends(get_session)):
    """Returns profile and role of currently logged-in user."""
    from app.auth.models import User
    user = session.scalar(select(User).where(User.id == current_user.id))
    return _to_user_out(user)

@router.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest, session: Session = Depends(get_session)):
    """Sends a 5-minute password reset link to user's email via Resend (AUTH-3)."""
    request_password_reset(session, data.email)
    session.commit()
    return {"message": "If this email is registered, a password reset link has been sent (expires in 5 minutes)."}

@router.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, session: Session = Depends(get_session)):
    """Resets user password using the single-use token."""
    reset_password_with_token(session, data.token, data.new_password)
    session.commit()
    return {"message": "Password has been successfully updated. You may now sign in."}

# ----------------- ADMIN STAFF MANAGEMENT (AUTH-5) -----------------

@router.post("/staff", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    data: StaffCreateRequest,
    current_user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Admin-only: Create a new staff account and send invitation email."""
    staff_user = create_staff_user(session, data)
    session.commit()
    return _to_user_out(staff_user)

@router.get("/staff", response_model=Page[UserOut])
def get_staff_list(
    params: PageParams = Depends(),
    current_user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Admin-only: List all staff members."""
    users, total = list_staff_users(session, params)
    return Page[UserOut](
        items=[_to_user_out(u) for u in users],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )

@router.patch("/staff/{staff_id}", response_model=UserOut)
def patch_staff(
    staff_id: str,
    data: StaffUpdateRequest,
    current_user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Admin-only: Update or deactivate a staff member."""
    updated = update_staff_user(session, staff_id, data)
    session.commit()
    return _to_user_out(updated)

# ----------------- CUSTOMER MANAGEMENT (ADMIN / STAFF) -----------------

@router.get("/customers", response_model=Page[CustomerOut])
def get_customers(
    params: PageParams = Depends(),
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    customers, total = list_customers(session, params)
    return Page[CustomerOut](
        items=[_to_customer_out(c) for c in customers],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )

@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreateRequest,
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    customer = create_customer_by_admin(session, data)
    session.commit()
    return _to_customer_out(customer)

@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer_by_id(
    customer_id: str,
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    customer = session.scalar(select(Customer).where(Customer.id == customer_id))
    if not customer:
        raise AppError(code="not_found", message="Customer not found", status_code=404)
    return _to_customer_out(customer)

# ----------------- CUSTOMER PORTAL PROFILE ROUTES -----------------

@portal_router.get("/me/profile", response_model=CustomerOut)
def get_my_profile(
    current_user: CurrentUser,
    session: Session = Depends(get_session)
):
    """Customer-only portal endpoint to view their own profile."""
    if not current_user.customer_id:
        raise AppError(code="not_found", message="No customer profile linked", status_code=404)
    customer = session.scalar(select(Customer).where(Customer.id == current_user.customer_id))
    if not customer:
        raise AppError(code="not_found", message="Customer profile not found", status_code=404)
    return _to_customer_out(customer)

@portal_router.patch("/me/profile", response_model=CustomerOut)
def update_my_profile(
    data: CustomerUpdateRequest,
    current_user: CurrentUser,
    session: Session = Depends(get_session)
):
    """Customer-only portal endpoint to update company name, phone, address."""
    if not current_user.customer_id:
        raise AppError(code="not_found", message="No customer profile linked", status_code=404)
    updated = update_customer_profile(session, current_user.customer_id, data)
    session.commit()
    return _to_customer_out(updated)
