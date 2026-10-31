from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENV: str = "dev"
    PORT: int = 8000
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000"
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

settings = Settings()
