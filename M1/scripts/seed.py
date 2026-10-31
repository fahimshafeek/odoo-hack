import argparse
from datetime import timedelta
from decimal import Decimal
from app.auth.models import Customer, User
from app.billing.models import Invoice
from app.catalog.models import Plan, Product
from app.core.clock import today
from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.payments.models import Payment
from app.subscriptions.models import Subscription, SubscriptionLine

def run_seed(reset: bool = False, perf: bool = False):
    session = SessionLocal()
    curr_date = today()

    if reset:
        print("[SEED] Resetting database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    print("[SEED] Creating demo accounts...")
    # 1. Admin
    admin = session.query(User).filter_by(email="admin@brightloop.test").first()
    if not admin:
        admin = User(
            email="admin@brightloop.test",
            password_hash=hash_password("BrightloopAdmin@123"),
            role="admin",
            full_name="System Administrator",
            is_active=True,
        )
        session.add(admin)

    # 2. Staff
    staff = session.query(User).filter_by(email="staff@brightloop.test").first()
    if not staff:
        staff = User(
            email="staff@brightloop.test",
            password_hash=hash_password("BrightloopStaff@123"),
            role="staff",
            full_name="Operations Staff",
            is_active=True,
        )
        session.add(staff)

    # 3. Customer
    cust_user = session.query(User).filter_by(email="customer@brightloop.test").first()
    if not cust_user:
        cust_user = User(
            email="customer@brightloop.test",
            password_hash=hash_password("BrightloopCust@123"),
            role="customer",
            full_name="Rohith Sarath",
            is_active=True,
        )
        session.add(cust_user)
        session.flush()

        customer_profile = Customer(
            user_id=cust_user.id,
            company_name="Apex Global Technologies",
            phone="+91 98765 43210",
            billing_address="102 Infopark Phase II, Kochi, Kerala, 682042",
            tax_id="32AABCA1234F1Z5",
        )
        session.add(customer_profile)
        session.flush()
    else:
        customer_profile = cust_user.customer_profile

    # 4. Catalog Products & Plans
    prod1 = Product(name="Brightloop ERP Core", sales_price=Decimal("1000.00"), cost_price=Decimal("300.00"))
    prod2 = Product(name="Advanced Analytics Seat", sales_price=Decimal("450.00"), cost_price=Decimal("100.00"))
    session.add_all([prod1, prod2])
    session.flush()

    plan_monthly = Plan(
        name="Pro Monthly",
        price=Decimal("2500.00"),
        billing_period="monthly",
        min_quantity=1,
        auto_close=False,
        allow_early_close=True,
        allow_pause=True,
        allow_renew=True,
    )
    plan_yearly = Plan(
        name="Enterprise Annual",
        price=Decimal("25000.00"),
        billing_period="yearly",
        min_quantity=1,
        auto_close=False,
        allow_early_close=False,
        allow_pause=True,
        allow_renew=True,
    )
    session.add_all([plan_monthly, plan_yearly])
    session.flush()

    # 5. Create Sample Subscriptions
    # Active Subscription 1 (Normal)
    sub1 = Subscription(
        number="SUB-2026-000001",
        customer_id=customer_profile.id,
        plan_id=plan_monthly.id,
        status="active",
        start_date=curr_date - timedelta(days=60),
        expiry_date=curr_date + timedelta(days=300),
        next_billing_date=curr_date + timedelta(days=30),
    )
    session.add(sub1)
    session.flush()

    sub1_line = SubscriptionLine(
        subscription_id=sub1.id,
        product_id=prod1.id,
        quantity=5,
        unit_price=Decimal("1000.00"),
        amount=Decimal("5000.00"),
    )
    session.add(sub1_line)

    # Active Subscription 2 (Expiring in 10 days for upcoming renewals report)
    sub2 = Subscription(
        number="SUB-2026-000002",
        customer_id=customer_profile.id,
        plan_id=plan_yearly.id,
        status="active",
        start_date=curr_date - timedelta(days=355),
        expiry_date=curr_date + timedelta(days=10),
        next_billing_date=curr_date + timedelta(days=10),
    )
    session.add(sub2)
    session.flush()

    # 6. Sample Invoices
    # Paid Invoice
    inv_paid = Invoice(
        number="INV-2026-000001",
        subscription_id=sub1.id,
        customer_id=customer_profile.id,
        status="paid",
        period_start=curr_date - timedelta(days=60),
        period_end=curr_date - timedelta(days=31),
        issue_date=curr_date - timedelta(days=60),
        due_date=curr_date - timedelta(days=45),
        subtotal=Decimal("7500.00"),
        tax_total=Decimal("1350.00"),
        total=Decimal("8850.00"),
        amount_paid=Decimal("8850.00"),
    )
    session.add(inv_paid)
    session.flush()

    pay1 = Payment(
        invoice_id=inv_paid.id,
        customer_id=customer_profile.id,
        method="bank_transfer",
        amount=Decimal("8850.00"),
        paid_on=curr_date - timedelta(days=50),
        note="NEFT payment settlement",
    )
    session.add(pay1)

    # Overdue Invoice (due 15 days ago, balance unpaid)
    inv_overdue = Invoice(
        number="INV-2026-000002",
        subscription_id=sub1.id,
        customer_id=customer_profile.id,
        status="confirmed",
        period_start=curr_date - timedelta(days=30),
        period_end=curr_date - timedelta(days=1),
        issue_date=curr_date - timedelta(days=30),
        due_date=curr_date - timedelta(days=15),
        subtotal=Decimal("7500.00"),
        tax_total=Decimal("1350.00"),
        total=Decimal("8850.00"),
        amount_paid=Decimal("2000.00"),  # Partially paid, remaining 6850.00 overdue
    )
    session.add(inv_overdue)
    session.flush()

    pay2 = Payment(
        invoice_id=inv_overdue.id,
        customer_id=customer_profile.id,
        method="card",
        amount=Decimal("2000.00"),
        paid_on=curr_date - timedelta(days=20),
        note="Initial partial card payment",
    )
    session.add(pay2)

    session.commit()
    print("[SEED] Successfully seeded database!")
    print("---------------------------------------------")
    print("Demo Admin:    admin@brightloop.test    / BrightloopAdmin@123")
    print("Demo Staff:    staff@brightloop.test    / BrightloopStaff@123")
    print("Demo Customer: customer@brightloop.test / BrightloopCust@123")
    print("---------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Brightloop Database")
    parser.add_argument("--reset", action="store_true", help="Reset all tables before seeding")
    parser.add_argument("--perf", action="store_true", help="Generate performance dataset")
    args = parser.parse_args()
    run_seed(reset=args.reset, perf=args.perf)
