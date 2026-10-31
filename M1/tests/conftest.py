import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.auth.models import Customer, User
from app.core.config import settings
from app.core.db import Base, get_session
from app.core.security import create_access_token, hash_password
from app.main import app

settings.ENV = "test"

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

@pytest.fixture(scope="function")
def session():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)

@pytest.fixture(scope="function")
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(session):
    def _headers(role: str = "customer", email: str | None = None):
        user_email = email or f"{role}_{id(role)}@test.com"
        user = User(
            email=user_email,
            password_hash=hash_password("Pass123!@#"),
            role=role,
            full_name=f"Test {role.capitalize()}",
            is_active=True,
        )
        session.add(user)
        session.flush()

        customer_id = None
        if role == "customer":
            cust = Customer(user_id=user.id, company_name="Test Co")
            session.add(cust)
            session.flush()
            customer_id = cust.id

        session.commit()
        token = create_access_token(user_id=user.id, role=role, customer_id=customer_id)
        return {"Authorization": f"Bearer {token}"}
    return _headers
