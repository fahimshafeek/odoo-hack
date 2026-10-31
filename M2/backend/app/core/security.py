import datetime
import uuid
from typing import Optional, Dict, Any
import jwt
from app.core.clock import now

SECRET_KEY = "brightloop-secret-key-change-in-prod"
ALGORITHM = "HS256"


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    customer_id: Optional[uuid.UUID] = None,
    full_name: str = "",
    email: str = "",
    expires_delta: Optional[datetime.timedelta] = None,
) -> str:
    expire = now() + (expires_delta or datetime.timedelta(hours=8))
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "full_name": full_name,
        "exp": expire,
    }
    if customer_id:
        payload["cid"] = str(customer_id)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
