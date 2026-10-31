import pytest
from app.auth.validators import validate_password_rules

def test_password_length_under_9_chars_fails():
    errors = validate_password_rules("Pass12@")
    assert any("at least 9 characters" in e for e in errors)

def test_password_valid_9_chars_passes():
    errors = validate_password_rules("Pass123!@")
    assert errors == []

def test_password_missing_uppercase_fails():
    errors = validate_password_rules("lowercase123!")
    assert any("uppercase" in e for e in errors)

def test_password_missing_lowercase_fails():
    errors = validate_password_rules("UPPERCASE123!")
    assert any("lowercase" in e for e in errors)

def test_password_missing_special_char_fails():
    errors = validate_password_rules("NoSpecialChar123")
    assert any("special character" in e for e in errors)

def test_password_cannot_equal_email():
    errors = validate_password_rules("User@1234!", email="User@1234!")
    assert any("identical to your email" in e for e in errors)
