from dataclasses import dataclass
from typing import Annotated
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import get_session
from app.core.errors import AppError
from app.core.security import decode_access_token

@dataclass
class AuthUser:
    id: str
    email: str
    role: str
    full_name: str
    customer_id: str | None = None

def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session)
) -> AuthUser:
    """Extracts and verifies the JWT token from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(code="unauthorized", message="Missing or invalid Authorization header", status_code=401)

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(code="unauthorized", message="Invalid token payload", status_code=401)

    # Lazy import to avoid circular dependency
    from app.auth.models import User
    user = session.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise AppError(code="unauthorized", message="User account not found or inactive", status_code=401)

    customer_id = None
    if user.customer_profile:
        customer_id = user.customer_profile.id

    return AuthUser(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        customer_id=customer_id
    )

CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

def require_role(*roles: str):
    """Dependency factory that checks if current user has one of the allowed roles."""
    def role_checker(current_user: CurrentUser) -> AuthUser:
        if current_user.role not in roles:
            raise AppError(
                code="forbidden",
                message=f"Access denied. Requires one of roles: {roles}",
                status_code=403
            )
        return current_user
    return role_checker

def scope_to_customer(stmt, customer_id_col, current_user: AuthUser):
    """Scopes a SQLAlchemy statement to only rows belonging to the authenticated customer."""
    if current_user.role == "customer":
        if not current_user.customer_id:
            raise AppError(code="not_found", message="Resource not found", status_code=404)
        return stmt.where(customer_id_col == current_user.customer_id)
    return stmt

def assert_customer_owns(current_user: AuthUser, customer_id: str | None) -> None:
    """Raises 404 (preventing id probing) if a customer attempts to access another customer's resource."""
    if current_user.role == "customer":
        if not customer_id or current_user.customer_id != customer_id:
            raise AppError(code="not_found", message="Resource not found", status_code=404)
