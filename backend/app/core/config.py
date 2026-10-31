from pathlib import Path
from zoneinfo import ZoneInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "dev"
    PORT: int = 8000
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    RATE_LIMIT_ENABLED: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./brightloop.db"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"

    # Security
    JWT_SECRET: str = "brightloop-secret-key-change-in-prod"
    JWT_EXPIRE_HOURS: int = 8
    PASSWORD_RESET_EXPIRE_MINUTES: int = 5

    # Email via Resend
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Hari <hakku@mail.laddu.cc>"

    # Bootstrap Admin
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@brightloop.test"
    BOOTSTRAP_ADMIN_PASSWORD: str = "BrightloopAdmin@123"

    # Razorpay Gateway
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"
    RAZORPAY_WEBHOOK_SECRET: str = ""


settings = Settings()

DATABASE_URL = settings.DATABASE_URL
RAZORPAY_KEY_ID = settings.RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET = settings.RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET = settings.RAZORPAY_WEBHOOK_SECRET
