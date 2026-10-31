import hashlib
from datetime import datetime, timedelta
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.clock import now
from app.core.config import settings
from app.core.errors import AppError

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False

def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a raw token to safely store in database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_access_token(
    user_id: str,
    role: str,
    customer_id: str | None = None,
    full_name: str | None = None,
    expires_delta: timedelta | None = None
) -> str:
    """Creates a signed JWT access token."""
    expire = now() + (expires_delta or timedelta(hours=settings.JWT_EXPIRE_HOURS))
    payload = {
        "sub": user_id,
        "role": role,
        "cid": customer_id,
        "name": full_name or "",
        "exp": expire,
        "iat": now(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AppError(code="unauthorized", message="Token has expired", status_code=401)
    except jwt.InvalidTokenError:
        raise AppError(code="unauthorized", message="Invalid token", status_code=401)
