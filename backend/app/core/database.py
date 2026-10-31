"""Database compatibility alias for app.core.db."""
from app.core.db import (
    Base,
    engine,
    SessionLocal,
    get_session,
    init_db,
    convention,
)

__all__ = ["Base", "engine", "SessionLocal", "get_session", "init_db", "convention"]
