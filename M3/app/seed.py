"""
Seed data generator for M3: Billing & Payments (B4 3.4).
Creates a realistic lifecycle mix:
  - Paid
  - Partially Paid
  - Outstanding (not overdue)
  - Overdue (balance > 0, due_date < today)
  - Draft
  - Cancelled
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core_compat import today
from app.database import SessionLocal, init_db
from app.engine import run_billing
from app.models import (
    Discount,
    Invoice,
    SubscriptionLineStub,
    SubscriptionStub,
    Tax,
)
from app.payments import record_payment
from app.schemas import PaymentCreate
from app.state import AuthUser, cancel_invoice, confirm_invoice


def seed_demo_data(session: Session) -> dict[str, int]:
    curr_date = today()
    admin_user = AuthUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="admin@brightloop.com",
        role="admin",
        full_name="Admin User",
    )

    # 1. Taxes
    taxes = [
        Tax(name="GST 18%", rate_percent=Decimal("18.00"), is_active=True),
        Tax(name="GST 5%", rate_percent=Decimal("5.00"), is_active=True),
        Tax(name="GST 0%", rate_percent=Decimal("0.00"), is_active=True),
    ]
    for t in taxes:
        existing = session.query(Tax).filter_by(name=t.name).first()
        if not existing:
            session.add(t)
    session.flush()

    # 2. Discounts (DISC-1, DISC-2, DISC-3)
    # Demo 10% subscription-scope discount with min_quantity=2 and usage_limit=2
    disc_10 = Discount(
        name="Launch Special 10%",
        type="percent",
        value=Decimal("10.00"),
        scope="subscription",
        min_quantity=2,
        usage_limit=2,
        used_count=0,
        start_date=curr_date - timedelta(days=60),
        end_date=curr_date + timedelta(days=60),
        is_active=True,
    )
    # Fixed ₹500 product-scope discount
    disc_fixed = Discount(
        name="Flat ₹500 Off",
        type="fixed",
        value=Decimal("500.00"),
        scope="product",
        start_date=curr_date - timedelta(days=30),
        end_date=curr_date + timedelta(days=30),
        is_active=True,
    )
    # Expired discount
    disc_expired = Discount(
        name="Early Bird 2025 (Expired)",
        type="percent",
        value=Decimal("15.00"),
        scope="subscription",
        start_date=curr_date - timedelta(days=120),
        end_date=curr_date - timedelta(days=30),
        is_active=True,
    )
    # Used up discount
    disc_used_up = Discount(
        name="Flash 50 (Sold Out)",
        type="fixed",
        value=Decimal("200.00"),
        scope="subscription",
        usage_limit=1,
        used_count=1,
        start_date=curr_date - timedelta(days=30),
        end_date=curr_date + timedelta(days=30),
        is_active=True,
    )
    session.add_all([disc_10, disc_fixed, disc_expired, disc_used_up])
    session.flush()

    # 3. Create demo subscriptions
    cust_alpha = uuid.UUID("11111111-1111-1111-1111-111111111111")
    cust_beta = uuid.UUID("22222222-2222-2222-2222-222222222222")
    cust_gamma = uuid.UUID("33333333-3333-3333-3333-333333333333")

    prod_cloud = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    prod_storage = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    # Subscription 1: Due in the past (will generate past invoices)
    sub1 = SubscriptionStub(
        number="SUB-2026-000001",
        customer_id=cust_alpha,
        status="active",
        billing_period="monthly",
        start_date=curr_date - timedelta(days=60),
        expiry_date=curr_date + timedelta(days=300),
        next_billing_date=curr_date - timedelta(days=60),
        plan_price=Decimal("1000.00"),
        plan_tax_rate=Decimal("18.00"),
        due_days=15,
        lines=[
            SubscriptionLineStub(
                product_id=prod_cloud,
                description="Cloud Hosting Pro",
                quantity=2,
                unit_price=Decimal("1500.00"),
                tax_rate=Decimal("18.00"),
                position=1,
            )
        ],
    )
    # Subscription 2: Another customer
    sub2 = SubscriptionStub(
        number="SUB-2026-000002",
        customer_id=cust_beta,
        status="active",
        billing_period="monthly",
        start_date=curr_date - timedelta(days=45),
        expiry_date=curr_date + timedelta(days=300),
        next_billing_date=curr_date - timedelta(days=45),
        plan_price=Decimal("500.00"),
        plan_tax_rate=Decimal("18.00"),
        due_days=10,
        lines=[
            SubscriptionLineStub(
                product_id=prod_storage,
                description="Extra 1TB NVMe Storage",
                quantity=3,
                unit_price=Decimal("400.00"),
                tax_rate=Decimal("18.00"),
                position=1,
            )
        ],
    )
    # Subscription 3: Due TODAY (for live demo testing "Run billing now")
    sub3 = SubscriptionStub(
        number="SUB-2026-000003",
        customer_id=cust_gamma,
        status="active",
        billing_period="daily",
        start_date=curr_date,
        expiry_date=curr_date + timedelta(days=30),
        next_billing_date=curr_date,
        plan_price=Decimal("100.00"),
        plan_tax_rate=Decimal("18.00"),
        due_days=5,
        lines=[
            SubscriptionLineStub(
                product_id=prod_cloud,
                description="Daily Compute Node",
                quantity=1,
                unit_price=Decimal("50.00"),
                tax_rate=Decimal("18.00"),
                position=1,
            )
        ],
    )
    session.add_all([sub1, sub2, sub3])
    session.commit()

    # 4. Run billing engine for past dates to create initial invoices
    run_billing(
        SessionLocal, as_of=curr_date - timedelta(days=30), triggered_by=admin_user.id
    )
    run_billing(
        SessionLocal, as_of=curr_date - timedelta(days=1), triggered_by=admin_user.id
    )

    # 5. Transition invoices to create lifecycle mix
    invoices = session.query(Invoice).order_by(Invoice.issue_date).all()
    for idx, inv in enumerate(invoices):
        if idx == 0:
            # Fully Paid
            confirm_invoice(session, inv, admin_user)
            record_payment(
                session,
                inv.id,
                PaymentCreate(
                    method="bank_transfer",
                    amount=inv.total,
                    paid_on=inv.issue_date + timedelta(days=2),
                ),
                admin_user,
            )
        elif idx == 1:
            # Partially Paid & Overdue
            inv.due_date = curr_date - timedelta(days=5)  # Make overdue
            confirm_invoice(session, inv, admin_user)
            record_payment(
                session,
                inv.id,
                PaymentCreate(
                    method="card",
                    amount=Decimal("500.00"),
                    paid_on=inv.issue_date + timedelta(days=3),
                ),
                admin_user,
            )
        elif idx == 2:
            # Confirmed (Outstanding, not overdue)
            inv.due_date = curr_date + timedelta(days=10)
            confirm_invoice(session, inv, admin_user)
        elif idx == 3:
            # Cancelled Draft
            cancel_invoice(session, inv, admin_user)

    session.commit()
    return {
        "taxes": len(taxes),
        "discounts": 4,
        "subscriptions": 3,
        "invoices": len(invoices),
    }


if __name__ == "__main__":
    init_db()
    with SessionLocal() as s:
        res = seed_demo_data(s)
        print("Seeded successfully:", res)
