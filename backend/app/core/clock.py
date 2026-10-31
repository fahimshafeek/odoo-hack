from datetime import UTC, date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
_FROZEN_DATE: Optional[date] = None


def set_frozen_today(d: Optional[date]) -> None:
    """Helper for testing to freeze or unfreeze today."""
    global _FROZEN_DATE
    _FROZEN_DATE = d


def now() -> datetime:
    """Returns current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def today() -> date:
    """Returns current date in Asia/Kolkata timezone, or frozen date if set."""
    if _FROZEN_DATE is not None:
        return _FROZEN_DATE
    return datetime.now(KOLKATA_TZ).date()
