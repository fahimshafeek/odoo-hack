import time
from collections import defaultdict
from fastapi import Request
from app.core.config import settings
from app.core.errors import AppError

# Sliding window storage: key -> list of timestamps
_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)

def check_login_rate_limit(request: Request, email: str, max_attempts: int = 5, window_seconds: int = 60) -> None:
    """Enforces 5 attempts per minute per IP and email combination."""
    if not settings.RATE_LIMIT_ENABLED:
        return

    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{email.strip().lower()}"
    current_time = time.time()

    # Prune old timestamps
    attempts = [ts for ts in _LOGIN_ATTEMPTS[key] if current_time - ts < window_seconds]
    _LOGIN_ATTEMPTS[key] = attempts

    if len(attempts) >= max_attempts:
        retry_after = int(window_seconds - (current_time - attempts[0]))
        raise AppError(
            code="rate_limited",
            message=f"Too many failed login attempts. Please try again in {retry_after} seconds.",
            status_code=429,
        )

def record_failed_login(request: Request, email: str) -> None:
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{email.strip().lower()}"
    _LOGIN_ATTEMPTS[key].append(time.time())

def clear_login_attempts(request: Request, email: str) -> None:
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{email.strip().lower()}"
    if key in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[key]
