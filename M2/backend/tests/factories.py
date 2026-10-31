import uuid
import datetime
from decimal import Decimal
from app.catalog.models import (
    Tax,
    Product,
    ProductAttribute,
    AttributeValue,
    Plan,
    PaymentTerm,
    QuotationTemplate,
    TemplateLine,
)
from app.core.models import Customer, User
from app.subscriptions.models import Subscription, SubscriptionLine


def create_test_tax(db, name="GST 18%", rate=Decimal("18.00")):
    tax = Tax(name=name, rate_percent=rate, is_active=True)
    db.add(tax)
    db.flush()
    return tax


def create_test_product(db, name="Odoo ERP", sales_price=Decimal("1000.00"), cost_price=Decimal("400.00"), tax_id=None):
    prod = Product(
        name=name,
        type="software",
        sales_price=sales_price,
        cost_price=cost_price,
        tax_id=tax_id,
        is_active=True,
    )
    db.add(prod)
    db.flush()

    attr_brand = ProductAttribute(product_id=prod.id, name="Brand")
    db.add(attr_brand)
    db.flush()

    val_odoo = AttributeValue(attribute_id=attr_brand.id, name="Odoo", extra_price=Decimal("560.00"))
    db.add(val_odoo)
    db.flush()

    return prod, attr_brand, val_odoo


def create_test_plan(
    db,
    name="Monthly Pro",
    price=Decimal("2000.00"),
    period="monthly",
    allow_pause=True,
    allow_renew=True,
    allow_early_close=True,
    auto_close=False,
    min_quantity=1,
    tax_id=None,
):
    plan = Plan(
        name=name,
        price=price,
        billing_period=period,
        min_quantity=min_quantity,
        allow_pause=allow_pause,
        allow_renew=allow_renew,
        allow_early_close=allow_early_close,
        auto_close=auto_close,
        tax_id=tax_id,
        is_active=True,
    )
    db.add(plan)
    db.flush()
    return plan


def create_test_payment_term(db, name="Net 30", due_days=30):
    term = PaymentTerm(name=name, due_days=due_days, is_active=True)
    db.add(term)
    db.flush()
    return term


def create_test_customer(db, company_name="Acme Corp"):
    user = User(
        email=f"customer_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="testhash",
        role="customer",
        full_name="Acme Rep",
    )
    db.add(user)
    db.flush()

    cust = Customer(
        user_id=user.id,
        company_name=company_name,
        phone="+919876543210",
        billing_address="123 High St, Mumbai",
    )
    db.add(cust)
    db.flush()
    return cust, user


def create_test_subscription(
    db,
    customer,
    plan,
    payment_term,
    status="draft",
    start_date=None,
    expiry_date=None,
    lines=None,
):
    start = start_date or datetime.date(2026, 1, 1)
    expiry = expiry_date or datetime.date(2027, 1, 1)
    sub = Subscription(
        number=f"SUB-2026-{uuid.uuid4().hex[:6]}",
        customer_id=customer.id,
        plan_id=plan.id,
        status=status,
        start_date=start,
        expiry_date=expiry,
        payment_term_id=payment_term.id,
        next_billing_date=start if status == "active" else None,
    )
    db.add(sub)
    db.flush()

    if lines:
        for idx, (prod, qty, u_price) in enumerate(lines):
            sline = SubscriptionLine(
                subscription_id=sub.id,
                product_id=prod.id,
                variant={"selections": []},
                quantity=qty,
                unit_price=u_price,
                amount=qty * u_price,
                tax_rate=Decimal("18.00"),
                position=idx,
            )
            db.add(sline)
        db.flush()

    return sub
