import datetime
from typing import Optional
import pytz

_TZ_KOLKATA = pytz.timezone("Asia/Kolkata")
_FROZEN_DATE: Optional[datetime.date] = None


def set_frozen_today(d: Optional[datetime.date]) -> None:
    """Helper for testing to freeze or unfreeze today."""
    global _FROZEN_DATE
    _FROZEN_DATE = d


def today() -> datetime.date:
    """Return today's date in Asia/Kolkata timezone, or frozen date if set."""
    if _FROZEN_DATE is not None:
        return _FROZEN_DATE
    return datetime.datetime.now(_TZ_KOLKATA).date()


def now() -> datetime.datetime:
    """Return current UTC timezone-aware timestamp."""
    return datetime.datetime.now(datetime.timezone.utc)
