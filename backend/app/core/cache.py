import functools
import time
from typing import Any, Callable

_CACHE: dict[str, tuple[float, Any]] = {}


def cached(prefix: str = "", ttl_seconds: int = 30):
    """Simple in-memory thread-safe TTL cache decorator."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [prefix or func.__name__, func.__name__]
            key_parts.extend(str(a) for a in args[1:])  # Skip session
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            now_ts = time.time()
            if cache_key in _CACHE:
                expiry, val = _CACHE[cache_key]
                if now_ts < expiry:
                    return val

            result = func(*args, **kwargs)
            _CACHE[cache_key] = (now_ts + ttl_seconds, result)
            return result

        return wrapper

    return decorator


def invalidate(prefix: str = "") -> None:
    """Invalidates cache entries matching prefix, or all if empty."""
    global _CACHE
    if not prefix:
        _CACHE.clear()
    else:
        _CACHE = {k: v for k, v in _CACHE.items() if not k.startswith(prefix)}
