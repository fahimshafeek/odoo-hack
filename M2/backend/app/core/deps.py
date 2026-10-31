import uuid
from typing import Annotated, Optional, Callable
from pydantic import BaseModel
from fastapi import Depends, Header
from app.core.errors import AppError
from app.core.security import decode_token


class AuthUser(BaseModel):
    id: uuid.UUID
    email: str
    role: str  # admin | staff | customer
    customer_id: Optional[uuid.UUID] = None
    full_name: str = ""


def get_current_user(authorization: Optional[str] = Header(None)) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("unauthorized", "Missing or invalid Authorization header", 401)
    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        role = payload.get("role")
        email = payload.get("email", "")
        full_name = payload.get("full_name", "")
        cid = payload.get("cid")
        if not sub or not role:
            raise AppError("unauthorized", "Malformed token", 401)
        return AuthUser(
            id=uuid.UUID(sub),
            email=email,
            role=role,
            customer_id=uuid.UUID(cid) if cid else None,
            full_name=full_name,
        )
    except AppError:
        raise
    except Exception as e:
        raise AppError("unauthorized", f"Invalid token: {e}", 401)


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def require_role(*roles: str) -> Callable[[AuthUser], AuthUser]:
    def dependency(user: CurrentUser) -> AuthUser:
        if user.role not in roles:
            raise AppError("forbidden", f"Role '{user.role}' not permitted for this operation", 403)
        return user

    return dependency


def scope_to_customer(stmt, customer_id_col, user: AuthUser):
    """Adds WHERE customer_id == user.customer_id for customers, no-op for staff/admin."""
    if user.role == "customer":
        if not user.customer_id:
            # Customer has no customer_id attached -> empty set
            return stmt.where(customer_id_col.is_(None))
        return stmt.where(customer_id_col == user.customer_id)
    return stmt


def assert_customer_owns(user: AuthUser, customer_id: uuid.UUID) -> None:
    """Raises 404 (not 403) on mismatch so IDs cannot be probed."""
    if user.role == "customer":
        if not user.customer_id or str(user.customer_id) != str(customer_id):
            raise AppError("not_found", "Resource not found", 404)
