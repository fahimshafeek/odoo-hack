from datetime import timedelta
import pytest
from app.auth.models import PasswordResetToken, User
from app.core.clock import now
from app.core.security import hash_token

def test_signup_success(client):
    res = client.post("/auth/signup", json={
        "email": "newcustomer@example.com",
        "password": "ValidPassword123!",
        "full_name": "John Doe",
        "company_name": "Doe Enterprises",
        "phone": "+91 99999 88888"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "customer"
    assert data["user"]["email"] == "newcustomer@example.com"

def test_signup_duplicate_email_fails(client):
    # First registration
    client.post("/auth/signup", json={
        "email": "unique@example.com",
        "password": "ValidPassword123!",
        "full_name": "User One"
    })
    # Duplicate with different casing
    res2 = client.post("/auth/signup", json={
        "email": "UNIQUE@example.com",
        "password": "ValidPassword123!",
        "full_name": "User Two"
    })
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "email_taken"

def test_signup_weak_password_fails(client):
    res = client.post("/auth/signup", json={
        "email": "weak@example.com",
        "password": "short",
        "full_name": "Short Pass"
    })
    assert res.status_code == 422

def test_login_success(client):
    client.post("/auth/signup", json={
        "email": "loginuser@example.com",
        "password": "ValidPassword123!",
        "full_name": "Login Test"
    })
    res = client.post("/auth/login", json={
        "email": "loginuser@example.com",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_wrong_password_fails(client):
    client.post("/auth/signup", json={
        "email": "wrongpw@example.com",
        "password": "ValidPassword123!",
        "full_name": "Wrong Test"
    })
    res = client.post("/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401

def test_forgot_and_reset_password(client, session):
    client.post("/auth/signup", json={
        "email": "resetme@example.com",
        "password": "OldPassword123!",
        "full_name": "Reset Test"
    })
    # Request forgot password
    res_forgot = client.post("/auth/forgot-password", json={"email": "resetme@example.com"})
    assert res_forgot.status_code == 200

    # Retrieve generated token from DB to test reset flow
    token_record = session.query(PasswordResetToken).first()
    assert token_record is not None
    assert token_record.used_at is None

    # Reset with valid token
    # Simulate a raw token that matches the hash
    raw_token = "test-raw-token-12345678901234567890"
    token_record.token_hash = hash_token(raw_token)
    session.commit()

    res_reset = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewValidPassword123!"
    })
    assert res_reset.status_code == 200

    # Login with new password
    res_login = client.post("/auth/login", json={
        "email": "resetme@example.com",
        "password": "NewValidPassword123!"
    })
    assert res_login.status_code == 200

def test_staff_cannot_create_staff(client, auth_headers):
    # Staff role attempting admin action
    headers = auth_headers(role="staff")
    res = client.post("/staff", json={"email": "newstaff@test.com", "full_name": "Staff B"}, headers=headers)
    assert res.status_code == 403

def test_admin_can_create_staff(client, auth_headers):
    # Admin role creates staff
    headers = auth_headers(role="admin")
    res = client.post("/staff", json={"email": "newstaff@test.com", "full_name": "Staff B"}, headers=headers)
    assert res.status_code == 201
    assert res.json()["role"] == "staff"

def test_customer_cannot_list_all_customers(client, auth_headers):
    # Customer attempts to view all customers -> 403
    headers = auth_headers(role="customer")
    res = client.get("/customers", headers=headers)
    assert res.status_code == 403
