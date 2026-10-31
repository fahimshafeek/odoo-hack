from datetime import date, datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def now() -> datetime:
    """Current UTC datetime (naive for universal SQLite compatibility)."""
    return datetime.utcnow()

def today() -> date:
    """Current date in company timezone (Asia/Kolkata)."""
    return datetime.now(IST).date()
