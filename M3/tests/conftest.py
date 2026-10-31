"""
Pytest configuration and fixtures for M3 tests.
Uses temporary SQLite database files for isolated tests.
"""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

import app.database as app_db
from app.core_compat import AuthUser
from app.database import Base, get_session
from app.main import app


@pytest.fixture
def db_engine():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_url = f"sqlite:///{tmp.name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    Base.metadata.create_all(bind=engine)

    orig_engine = app_db.engine
    orig_sessionlocal = app_db.SessionLocal
    app_db.engine = engine
    app_db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield engine

    app_db.engine = orig_engine
    app_db.SessionLocal = orig_sessionlocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(tmp.name):
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@pytest.fixture
def db_session_factory(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture
def db(db_session_factory):
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def admin_user():
    return AuthUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="admin@brightloop.com",
        role="admin",
        full_name="Admin User",
    )


@pytest.fixture
def staff_user():
    return AuthUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        email="staff@brightloop.com",
        role="staff",
        full_name="Staff User",
    )


@pytest.fixture
def customer_user():
    return AuthUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        email="customer@example.com",
        role="customer",
        customer_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        full_name="Customer User",
    )


@pytest.fixture
def client(db_engine):
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
