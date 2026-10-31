import os
import glob
from app.core.db import init_db, SessionLocal
from app.auth.models import User
from app.core.security import hash_password

def reset_to_clean():
    # Remove existing sqlite files to avoid lock/foreign key issues
    for f in glob.glob("brightloop.db*"):
        try:
            os.remove(f)
        except OSError:
            pass

    # Initialize fresh tables
    init_db()

    # Seed the single primary Administrator
    session = SessionLocal()
    admin = User(
        email="admin@brightloop.io",
        password_hash=hash_password("BrightloopAdmin@123"),
        role="admin",
        full_name="System Administrator",
        is_active=True,
    )
    session.add(admin)
    session.commit()
    print("Database cleanly reset to 0 with 1 Admin account:")
    print("Email:    admin@brightloop.io")
    print("Password: BrightloopAdmin@123")

if __name__ == "__main__":
    reset_to_clean()
