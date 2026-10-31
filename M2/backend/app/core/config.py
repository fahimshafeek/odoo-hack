import os
from pathlib import Path
from dotenv import load_dotenv

# Search and load .env files
base_dir = Path(__file__).resolve().parent.parent.parent
for env_file in [base_dir / ".env", Path.cwd() / ".env"]:
    if env_file.is_file():
        load_dotenv(env_file)
        break

APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./brightloop.db")
SECRET_KEY = os.getenv("SECRET_KEY", "brightloop-secret-key-change-in-prod")
BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@brightloop.local")
BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123")
