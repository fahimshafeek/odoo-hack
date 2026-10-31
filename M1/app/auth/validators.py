import re
from app.core.errors import AppError

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{9,}$")

def validate_password_rules(password: str, email: str | None = None) -> list[str]:
    """
    Validates password complexity against requirements:
    - Minimum 9 characters (more than 8)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one special character
    - Cannot equal email
    """
    errors = []
    if len(password) < 9:
        errors.append("Password must be at least 9 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one special character.")
    if email and password.strip().lower() == email.strip().lower():
        errors.append("Password cannot be identical to your email address.")
    if len(password) > 128:
        errors.append("Password cannot exceed 128 characters.")
    return errors

def validate_password_or_raise(password: str, email: str | None = None) -> None:
    errors = validate_password_rules(password, email)
    if errors:
        raise AppError(
            code="validation_error",
            message="Password does not meet security requirements.",
            status_code=422,
            fields={"password": " ".join(errors)}
        )
