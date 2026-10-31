import uuid
from dataclasses import dataclass
from typing import Annotated, Callable, Optional
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import get_session
from app.core.errors import AppError
from app.core.security import decode_access_token


@dataclass
class AuthUser:
    id: uuid.UUID
    email: str
    role: str  # admin | staff | customer
    customer_id: Optional[uuid.UUID] = None
    full_name: str = ""


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    session: Session = Depends(get_session),
) -> AuthUser:
    """Extracts and verifies JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(code="unauthorized", message="Missing or invalid Authorization header", status_code=401)

    token = authorization.split("Bearer ", 1)[1].strip()
    payload = decode_access_token(token)

    sub = payload.get("sub")
    if not sub:
        raise AppError(code="unauthorized", message="Invalid token payload", status_code=401)

    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError):
        raise AppError(code="unauthorized", message="Invalid user id in token", status_code=401)

    # Check database to ensure user is active
    from app.auth.models import User
    user = session.get(User, user_uuid)
    if not user or not user.is_active:
        raise AppError(code="unauthorized", message="User account not found or inactive", status_code=401)

    cust_id = None
    if user.customer_profile:
        cust_id = user.customer_profile.id
    elif payload.get("cid"):
        try:
            cust_id = uuid.UUID(str(payload.get("cid")))
        except (ValueError, TypeError):
            pass

    return AuthUser(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name or "",
        customer_id=cust_id,
    )


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def require_role(*roles: str) -> Callable[[AuthUser], AuthUser]:
    """Dependency factory checking if current user has an allowed role."""
    def dependency(user: CurrentUser) -> AuthUser:
        if user.role not in roles:
            raise AppError(
                code="forbidden",
                message=f"Access denied. Requires one of roles: {roles}",
                status_code=403,
            )
        return user

    return dependency


def scope_to_customer(stmt, customer_id_col, user: AuthUser):
    """Filters query to customer_id if user is customer; no-op for staff/admin."""
    if user.role == "customer":
        if not user.customer_id:
            return stmt.where(customer_id_col.is_(None))
        return stmt.where(customer_id_col == user.customer_id)
    return stmt


def assert_customer_owns(user: AuthUser, customer_id: uuid.UUID) -> None:
    """Verifies that a customer owns a target resource (returns 404 per D21 to avoid ID enumeration)."""
    if user.role == "customer":
        if not user.customer_id or user.customer_id != customer_id:
            raise AppError("not_found", "Resource not found", status_code=404)
