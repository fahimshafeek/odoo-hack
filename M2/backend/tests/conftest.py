import os
import uuid
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.core.database import Base, get_session
from app.core.models import User, Customer
from app.core.security import create_access_token
from app.core.clock import set_frozen_today
from app.main import app

# Use in-memory SQLite with StaticPool so all threads/sessions share the same DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    set_frozen_today(None)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def _make(role: str = "admin", customer_id: uuid.UUID = None, email: str = None, full_name: str = None):
        u_id = uuid.uuid4()
        u_email = email or f"{role}_{u_id.hex[:6]}@example.com"
        user = User(
            id=u_id,
            email=u_email,
            password_hash="testhash",
            role=role,
            full_name=full_name or f"Test {role.capitalize()}",
            is_active=True,
        )
        db.add(user)

        if role == "customer" and not customer_id:
            cust = Customer(
                id=uuid.uuid4(),
                user_id=user.id,
                company_name=f"Company {u_id.hex[:4]}",
            )
            db.add(cust)
            db.flush()
            customer_id = cust.id

        db.flush()
        return user, customer_id

    return _make


@pytest.fixture
def auth_headers(make_user):
    def _headers(role: str = "admin", customer_id: uuid.UUID = None):
        user, cid = make_user(role=role, customer_id=customer_id)
        token = create_access_token(
            user_id=user.id,
            role=role,
            customer_id=cid,
            full_name=user.full_name,
            email=user.email,
        )
        return {"Authorization": f"Bearer {token}"}, user, cid

    return _headers


@pytest.fixture
def frozen_today():
    def _freeze(d: datetime.date):
        set_frozen_today(d)

    yield _freeze
    set_frozen_today(None)
