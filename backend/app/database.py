"""Compatibility proxy for app.database."""
from app.core.db import Base, engine, SessionLocal, get_session, init_db

__all__ = ["Base", "engine", "SessionLocal", "get_session", "init_db"]
