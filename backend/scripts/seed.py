import argparse
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from app.core.clock import today
from app.core.db import Base, SessionLocal, engine, init_db
from app.core.security import hash_password
from app.core.deps import AuthUser
from app.auth.models import Customer, User
from app.catalog.models import Tax
from app.billing.models import (
    Discount,
    DiscountTarget,
    Invoice,
    InvoiceLine,
)
from app.payments.models import Payment
from app.payments.service import record_payment
from app.billing.schemas import PaymentCreate
from app.billing.state import confirm_invoice, cancel_invoice
from scripts.seed_parts.catalog_subs import seed as seed_catalog_subs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("brightloop.seed")


def run_seed(reset: bool = False):
    if reset:
        logger.info("Dropping and recreating all tables...")
        init_db(reset=True)
    else:
        init_db()

    session = SessionLocal()
    curr_date = today()
    try:
        logger.info("1. Seeding base users and customer profiles...")
        admin = session.query(User).filter_by(email="admin@brightloop.io").first()
        if not admin:
            admin = User(
                email="admin@brightloop.io",
                password_hash=hash_password("BrightloopAdmin@123"),
                role="admin",
                full_name="System Administrator",
                is_active=True,
            )
            session.add(admin)

        staff = session.query(User).filter_by(email="staff@brightloop.io").first()
        if not staff:
            staff = User(
                email="staff@brightloop.io",
                password_hash=hash_password("BrightloopStaff@123"),
                role="staff",
                full_name="Operations Staff",
                is_active=True,
            )
            session.add(staff)

        cust_user = session.query(User).filter_by(email="customer@brightloop.io").first()
        if not cust_user:
            cust_user = User(
                email="customer@brightloop.io",
                password_hash=hash_password("BrightloopCust@123"),
                role="customer",
                full_name="Rohith Sarath",
                is_active=True,
            )
            session.add(cust_user)
            session.flush()

            cust_profile = Customer(
                user_id=cust_user.id,
                company_name="Acme Corporation Ltd",
                phone="+91 98765 43210",
                billing_address="Plot 42, Tech Park, Bangalore, Karnataka 560001",
                tax_id="29ABCDE1234F1Z5",
            )
            session.add(cust_profile)

        session.commit()

        logger.info("2. Seeding catalog, products, plans, and subscriptions...")
        counts = seed_catalog_subs(session)
        logger.info("Catalog seeded: %s", counts)

        logger.info("3. Seeding discounts and billing data...")
        # Seed Discounts
        disc_10 = session.query(Discount).filter_by(name="Launch Special 10%").first()
        if not disc_10:
            disc_10 = Discount(
                name="Launch Special 10%",
                type="percent",
                value=Decimal("10.00"),
                scope="subscription",
                min_quantity=1,
                start_date=curr_date - timedelta(days=90),
                end_date=curr_date + timedelta(days=90),
                usage_limit=100,
                used_count=0,
                is_active=True,
            )
            session.add(disc_10)
            session.flush()

        session.commit()
        logger.info("Database seeding complete!")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed Brightloop database")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()
    run_seed(reset=args.reset)


if __name__ == "__main__":
    main()
