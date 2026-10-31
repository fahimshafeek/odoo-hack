import os

APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./brightloop.db")
SECRET_KEY = os.getenv("SECRET_KEY", "brightloop-secret-key-change-in-prod")
