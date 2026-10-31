import uuid
import datetime
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.clock import today as get_today
from app.core.deps import AuthUser
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
from app.subscriptions.service import create_subscription
from app.subscriptions.state import transition
from app.subscriptions.schemas import SubscriptionCreate, SubscriptionLineInput

logger = logging.getLogger("brightloop.seed.catalog_subs")


def seed(session) -> dict:
    """
    Seed ~12 products with variants (incl. Odoo ERP: 1000 + Brand Odoo +560),
    taxes, payment terms, 5 plans (one with price=0), 4 templates, and ~30 realistic subscriptions.
    """
    today = get_today()
    admin_user = session.execute(select(User).where(User.role == "admin")).scalars().first()
    if not admin_user:
        admin_user = User(
            email="admin@brightloop.local",
            password_hash="adminhash",
            role="admin",
            full_name="System Admin",
        )
        session.add(admin_user)
        session.flush()

    admin_auth = AuthUser(
        id=admin_user.id,
        email=admin_user.email,
        role=admin_user.role,
        full_name=admin_user.full_name,
    )

    # 1. Taxes
    taxes_data = [
        ("GST 0% Exempt", Decimal("0.00")),
        ("GST 5%", Decimal("5.00")),
        ("GST 12%", Decimal("12.00")),
        ("GST 18%", Decimal("18.00")),
    ]
    taxes = {}
    for name, rate in taxes_data:
        tax = session.execute(select(Tax).where(Tax.name == name)).scalar_one_or_none()
        if not tax:
            tax = Tax(name=name, rate_percent=rate, is_active=True)
            session.add(tax)
            session.flush()
        taxes[name] = tax

    # 2. Payment terms
    terms_data = [
        ("Immediate", 0),
        ("Net 15", 15),
        ("Net 30", 30),
        ("Net 60", 60),
    ]
    payment_terms = {}
    for name, days in terms_data:
        term = session.execute(select(PaymentTerm).where(PaymentTerm.name == name)).scalar_one_or_none()
        if not term:
            term = PaymentTerm(name=name, due_days=days, is_active=True)
            session.add(term)
            session.flush()
        payment_terms[name] = term

    # 3. Products & Variants (~12 products)
    tax_18 = taxes["GST 18%"]
    tax_5 = taxes["GST 5%"]
    products_spec = [
        {
            "name": "Odoo ERP",
            "type": "software",
            "sales_price": Decimal("1000.00"),
            "cost_price": Decimal("350.00"),
            "tax": tax_18,
            "attrs": [
                ("Brand", [("Odoo", Decimal("560.00")), ("Brightloop Custom", Decimal("200.00")), ("Community", Decimal("0.00"))]),
                ("Deployment", [("Cloud Multi-tenant", Decimal("0.00")), ("Dedicated Cloud", Decimal("800.00"))]),
            ],
        },
        {
            "name": "User Seat License",
            "type": "license",
            "sales_price": Decimal("250.00"),
            "cost_price": Decimal("80.00"),
            "tax": tax_18,
            "attrs": [
                ("Tier", [("Standard", Decimal("0.00")), ("Power User", Decimal("150.00"))]),
            ],
        },
        {
            "name": "Cloud Storage 500GB",
            "type": "infrastructure",
            "sales_price": Decimal("500.00"),
            "cost_price": Decimal("200.00"),
            "tax": tax_18,
            "attrs": [
                ("Backup SLA", [("Daily", Decimal("0.00")), ("Continuous Mirror", Decimal("350.00"))]),
            ],
        },
        {
            "name": "Priority Support SLA",
            "type": "service",
            "sales_price": Decimal("1500.00"),
            "cost_price": Decimal("600.00"),
            "tax": tax_18,
            "attrs": [
                ("Response Time", [("4 Hours", Decimal("0.00")), ("1 Hour 24/7", Decimal("1200.00"))]),
            ],
        },
        {
            "name": "Advanced Analytics Module",
            "type": "software",
            "sales_price": Decimal("800.00"),
            "cost_price": Decimal("250.00"),
            "tax": tax_18,
            "attrs": [
                ("AI Forecasting", [("Included", Decimal("400.00")), ("Basic", Decimal("0.00"))]),
            ],
        },
        {
            "name": "Custom Domain & SSL",
            "type": "infrastructure",
            "sales_price": Decimal("150.00"),
            "cost_price": Decimal("40.00"),
            "tax": tax_18,
            "attrs": [],
        },
        {
            "name": "POS Terminal Integration",
            "type": "hardware_addon",
            "sales_price": Decimal("900.00"),
            "cost_price": Decimal("500.00"),
            "tax": tax_18,
            "attrs": [
                ("Terminal Model", [("Pax A920", Decimal("300.00")), ("Verifone V240m", Decimal("200.00"))]),
            ],
        },
        {
            "name": "E-Commerce Sync Engine",
            "type": "software",
            "sales_price": Decimal("650.00"),
            "cost_price": Decimal("200.00"),
            "tax": tax_18,
            "attrs": [
                ("Platform", [("Shopify", Decimal("0.00")), ("WooCommerce", Decimal("0.00")), ("Magento", Decimal("300.00"))]),
            ],
        },
        {
            "name": "Automated Tax Filing Helper",
            "type": "service",
            "sales_price": Decimal("400.00"),
            "cost_price": Decimal("150.00"),
            "tax": tax_18,
            "attrs": [],
        },
        {
            "name": "Weekly Data Export",
            "type": "service",
            "sales_price": Decimal("100.00"),
            "cost_price": Decimal("20.00"),
            "tax": tax_18,
            "attrs": [],
        },
        {
            "name": "Dedicated Account Manager",
            "type": "service",
            "sales_price": Decimal("3000.00"),
            "cost_price": Decimal("1500.00"),
            "tax": tax_18,
            "attrs": [],
        },
        {
            "name": "Essential Starter Kit",
            "type": "bundle",
            "sales_price": Decimal("750.00"),
            "cost_price": Decimal("300.00"),
            "tax": tax_5,
            "attrs": [],
        },
    ]

    products = {}
    for ps in products_spec:
        prod = session.execute(select(Product).where(Product.name == ps["name"])).scalar_one_or_none()
        if not prod:
            prod = Product(
                name=ps["name"],
                type=ps["type"],
                sales_price=ps["sales_price"],
                cost_price=ps["cost_price"],
                tax_id=ps["tax"].id if ps["tax"] else None,
                is_active=True,
            )
            session.add(prod)
            session.flush()

            for attr_name, vals in ps["attrs"]:
                pattr = ProductAttribute(product_id=prod.id, name=attr_name)
                session.add(pattr)
                session.flush()
                for val_name, extra in vals:
                    aval = AttributeValue(attribute_id=pattr.id, name=val_name, extra_price=extra)
                    session.add(aval)
            session.flush()
        products[ps["name"]] = prod

    # 4. Plans (5-6 plans with various periods & rule flags, one with price=0)
    plans_spec = [
        {
            "name": "Basic Monthly",
            "price": Decimal("1500.00"),
            "billing_period": "monthly",
            "min_quantity": 1,
            "allow_pause": True,
            "allow_renew": True,
            "allow_early_close": True,
            "auto_close": False,
            "tax": tax_18,
        },
        {
            "name": "Enterprise Yearly",
            "price": Decimal("15000.00"),
            "billing_period": "yearly",
            "min_quantity": 5,
            "allow_pause": False,
            "allow_renew": True,
            "allow_early_close": True,
            "auto_close": False,
            "tax": tax_18,
        },
        {
            "name": "Weekly Sprint",
            "price": Decimal("400.00"),
            "billing_period": "weekly",
            "min_quantity": 1,
            "allow_pause": True,
            "allow_renew": True,
            "allow_early_close": True,
            "auto_close": True,
            "tax": tax_18,
        },
        {
            "name": "Daily Demo Plan",
            "price": Decimal("50.00"),
            "billing_period": "daily",
            "min_quantity": 1,
            "allow_pause": True,
            "allow_renew": True,
            "allow_early_close": True,
            "auto_close": True,
            "tax": tax_18,
        },
        {
            "name": "Pay-As-You-Go (Zero Base Fee)",
            "price": Decimal("0.00"),  # plan price 0 means lines only
            "billing_period": "monthly",
            "min_quantity": 1,
            "allow_pause": True,
            "allow_renew": True,
            "allow_early_close": True,
            "auto_close": False,
            "tax": tax_18,
        },
    ]

    plans = {}
    for p_spec in plans_spec:
        plan = session.execute(select(Plan).where(Plan.name == p_spec["name"])).scalar_one_or_none()
        if not plan:
            plan = Plan(
                name=p_spec["name"],
                price=p_spec["price"],
                billing_period=p_spec["billing_period"],
                min_quantity=p_spec["min_quantity"],
                allow_pause=p_spec["allow_pause"],
                allow_renew=p_spec["allow_renew"],
                allow_early_close=p_spec["allow_early_close"],
                auto_close=p_spec["auto_close"],
                tax_id=p_spec["tax"].id if p_spec["tax"] else None,
                is_active=True,
            )
            session.add(plan)
            session.flush()
        plans[p_spec["name"]] = plan

    # 5. Quotation Templates
    templates_spec = [
        ("SME Standard ERP Starter", plans["Basic Monthly"], 30, [("Odoo ERP", 1), ("User Seat License", 3)]),
        ("Enterprise Full Cloud Suite", plans["Enterprise Yearly"], 45, [("Odoo ERP", 1), ("User Seat License", 10), ("Priority Support SLA", 1)]),
        ("Fast Track Onboarding", plans["Weekly Sprint"], 14, [("Essential Starter Kit", 1)]),
        ("Modular Custom Cloud", plans["Pay-As-You-Go (Zero Base Fee)"], 30, [("Cloud Storage 500GB", 2), ("Advanced Analytics Module", 1)]),
    ]
    templates = {}
    for t_name, t_plan, v_days, line_items in templates_spec:
        tpl = session.execute(select(QuotationTemplate).where(QuotationTemplate.name == t_name)).scalar_one_or_none()
        if not tpl:
            tpl = QuotationTemplate(
                name=t_name,
                plan_id=t_plan.id,
                validity_days=v_days,
                is_active=True,
            )
            session.add(tpl)
            session.flush()

            for idx, (p_name, qty) in enumerate(line_items):
                p = products[p_name]
                tline = TemplateLine(
                    template_id=tpl.id,
                    product_id=p.id,
                    variant={"value_ids": []},
                    quantity=qty,
                    position=idx,
                    tax_id=p.tax_id,
                )
                session.add(tline)
            session.flush()
        templates[t_name] = tpl

    # 6. Customers (~6 realistic sample customers)
    customers_data = [
        ("Tata Consultancy Group", "tata@brightloop.local", "9820011223"),
        ("Reliance Digital Works", "reliance@brightloop.local", "9820044556"),
        ("Infosys Solutions Ltd", "infosys@brightloop.local", "9820077889"),
        ("Wipro Enterprises", "wipro@brightloop.local", "9820033221"),
        ("HDFC Financial Services", "hdfc@brightloop.local", "9820066554"),
        ("Zomato Tech Hub", "zomato@brightloop.local", "9820099887"),
    ]
    customers = []
    for comp, email, phone in customers_data:
        cust = session.execute(select(Customer).where(Customer.company_name == comp)).scalar_one_or_none()
        if not cust:
            c_user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not c_user:
                c_user = User(
                    email=email,
                    password_hash="custhash",
                    role="customer",
                    full_name=f"{comp} Admin",
                )
                session.add(c_user)
                session.flush()

            cust = Customer(
                user_id=c_user.id,
                company_name=comp,
                phone=phone,
                billing_address=f"Tech Tower, {comp}, Mumbai",
            )
            session.add(cust)
            session.flush()
        customers.append(cust)

    # 7. Subscriptions (~30 realistic subscriptions across all statuses)
    existing_subs_count = session.execute(select(Subscription)).scalars().all()
    if len(existing_subs_count) < 25:
        target_plan = plans["Basic Monthly"]
        target_term = payment_terms["Net 30"]
        odoo_prod = session.execute(
            select(Product)
            .options(selectinload(Product.attributes).selectinload(ProductAttribute.values))
            .where(Product.name == "Odoo ERP")
        ).scalar_one()

        # Find Odoo variant value ID for the 560 extra
        val_odoo_obj = None
        for attr in odoo_prod.attributes:
            for v in attr.values:
                if v.name == "Odoo":
                    val_odoo_obj = v
                    break

        variant_ids = [val_odoo_obj.id] if val_odoo_obj else []

        # Generate subscriptions in various statuses:
        # - Drafts: 4
        # - Quotations: 5
        # - Confirmed: 4
        # - Active due for billing: 10
        # - Paused: 3
        # - Closed: 3
        # - Upcoming renewals: 3
        distribution = [
            ("draft", 4),
            ("quotation", 5),
            ("confirmed", 4),
            ("active_due", 10),
            ("paused", 3),
            ("closed", 3),
            ("upcoming_renewal", 3),
        ]

        sub_idx = 1
        for status_type, count in distribution:
            for _ in range(count):
                cust = customers[sub_idx % len(customers)]
                start_d = today - datetime.timedelta(days=(sub_idx * 15))
                expiry_d = start_d + datetime.timedelta(days=365)

                if status_type == "upcoming_renewal":
                    # Expiring within 20 days
                    expiry_d = today + datetime.timedelta(days=15)
                    start_d = expiry_d - datetime.timedelta(days=365)

                lines_in = [
                    SubscriptionLineInput(
                        product_id=odoo_prod.id,
                        quantity=2,
                        variant_value_ids=variant_ids,
                    )
                ]

                create_data = SubscriptionCreate(
                    customer_id=cust.id,
                    plan_id=target_plan.id,
                    start_date=start_d,
                    expiry_date=expiry_d,
                    payment_term_id=target_term.id,
                    lines=lines_in,
                )

                sub_detail = create_subscription(session, create_data, admin_auth)
                sub_obj = session.get(Subscription, sub_detail.id)

                if status_type == "quotation":
                    transition(session, sub_obj, "send_quote", admin_auth)
                elif status_type == "confirmed":
                    transition(session, sub_obj, "send_quote", admin_auth)
                    transition(session, sub_obj, "confirm", admin_auth)
                elif status_type in ("active_due", "upcoming_renewal"):
                    transition(session, sub_obj, "send_quote", admin_auth)
                    transition(session, sub_obj, "confirm", admin_auth)
                    transition(session, sub_obj, "activate", admin_auth)
                    # Next billing date set to today or earlier so billing run has due subscriptions
                    sub_obj.next_billing_date = today - datetime.timedelta(days=2)
                elif status_type == "paused":
                    transition(session, sub_obj, "send_quote", admin_auth)
                    transition(session, sub_obj, "confirm", admin_auth)
                    transition(session, sub_obj, "activate", admin_auth)
                    transition(session, sub_obj, "pause", admin_auth)
                elif status_type == "closed":
                    transition(session, sub_obj, "send_quote", admin_auth)
                    transition(session, sub_obj, "confirm", admin_auth)
                    transition(session, sub_obj, "activate", admin_auth)
                    transition(session, sub_obj, "close", admin_auth)

                session.flush()
                sub_idx += 1

    session.commit()
    logger.info("Seed completed successfully!")
    return {
        "taxes": len(taxes),
        "payment_terms": len(payment_terms),
        "products": len(products),
        "plans": len(plans),
        "templates": len(templates),
        "customers": len(customers),
    }
