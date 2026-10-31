import uuid
import datetime
from decimal import Decimal
import pytest
from app.subscriptions.models import Subscription
from tests.factories import (
    create_test_tax,
    create_test_product,
    create_test_plan,
    create_test_payment_term,
    create_test_customer,
    create_test_subscription,
)


def test_price_preview_endpoint(client, auth_headers, db):
    headers, _, _ = auth_headers("staff")
    tax = create_test_tax(db, rate=Decimal("18.00"))
    prod, attr, val = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db, price=Decimal("2000.00"), tax_id=tax.id, min_quantity=1)

    payload = {
        "plan_id": str(plan.id),
        "lines": [
            {
                "product_id": str(prod.id),
                "quantity": 2,
                "variant_value_ids": [str(val.id)],
                "tax_id": str(tax.id),
            }
        ],
    }
    res = client.post("/subscriptions/price-preview", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Line: unit price = 1000 + 560 = 1560.00
    # Amount for qty 2 = 3120.00
    # Line tax 18% of 3120 = 561.60 -> line total = 3681.60
    assert data["lines"][0]["unit_price"] == "1560.00"
    assert data["lines"][0]["amount"] == "3120.00"
    assert data["lines"][0]["tax_amount"] == "561.60"
    assert data["lines"][0]["total"] == "3681.60"

    # Plan fee: 2000.00 + 18% tax 360.00 = 2360.00
    assert data["plan_fee"]["amount"] == "2000.00"
    assert data["plan_fee"]["tax_amount"] == "360.00"
    assert data["plan_fee"]["total"] == "2360.00"

    # Grand totals:
    # Subtotal = 3120 + 2000 = 5120.00
    # Tax total = 561.60 + 360 = 921.60
    # Total = 6041.60
    assert data["totals"]["subtotal"] == "5120.00"
    assert data["totals"]["tax_total"] == "921.60"
    assert data["totals"]["total"] == "6041.60"


def test_subscription_create_and_detail(client, auth_headers, db):
    headers, _, _ = auth_headers("staff")
    tax = create_test_tax(db)
    prod, attr, val = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    payload = {
        "customer_id": str(cust.id),
        "plan_id": str(plan.id),
        "start_date": "2026-05-01",
        "expiry_date": "2027-05-01",
        "payment_term_id": str(term.id),
        "lines": [
            {
                "product_id": str(prod.id),
                "quantity": 1,
                "variant_value_ids": [str(val.id)],
            }
        ],
    }
    res = client.post("/subscriptions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["number"].startswith("SUB-2026-")
    assert len(data["lines"]) == 1
    assert data["lines"][0]["unit_price"] == "1560.00"
    sub_id = data["id"]

    # Get detail
    res = client.get(f"/subscriptions/{sub_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["can_edit"] is True
    assert "send_quote" in res.json()["allowed_actions"]


def test_d26_create_from_template(client, auth_headers, db):
    admin_headers, _, _ = auth_headers("admin")
    staff_headers, _, _ = auth_headers("staff")
    tax = create_test_tax(db)
    prod, attr, val = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    create_test_payment_term(db, name="Immediate", due_days=0)
    cust, _ = create_test_customer(db)

    # Create quotation template (Admin only)
    tpl_payload = {
        "name": "Standard Cloud Pack",
        "plan_id": str(plan.id),
        "validity_days": 30,
        "lines": [
            {
                "product_id": str(prod.id),
                "quantity": 3,
                "variant_value_ids": [str(val.id)],
            }
        ],
    }
    res_tpl = client.post("/quotation-templates", json=tpl_payload, headers=admin_headers)
    assert res_tpl.status_code == 201
    tpl_id = res_tpl.json()["id"]

    # Create subscription from template (Staff can create subscriptions)
    from_tpl_payload = {"customer_id": str(cust.id)}
    res = client.post(f"/subscriptions/from-template/{tpl_id}", json=from_tpl_payload, headers=staff_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["template_id"] == tpl_id
    assert len(data["lines"]) == 1
    assert data["lines"][0]["quantity"] == 3
    assert data["lines"][0]["unit_price"] == "1560.00"


def test_customer_portal_scoping_and_404(client, auth_headers, db):
    # Customer A
    cust_a, user_a = create_test_customer(db, "Customer Alpha")
    headers_a, _, _ = auth_headers("customer", customer_id=cust_a.id)

    # Customer B
    cust_b, user_b = create_test_customer(db, "Customer Beta")
    headers_b, _, _ = auth_headers("customer", customer_id=cust_b.id)

    plan = create_test_plan(db, allow_pause=True)
    term = create_test_payment_term(db)
    prod, _, _ = create_test_product(db)

    # Sub A (active)
    sub_a = create_test_subscription(db, cust_a, plan, term, status="active", lines=[(prod, 1, Decimal("1000.00"))])
    # Sub B (draft)
    sub_b_draft = create_test_subscription(db, cust_b, plan, term, status="draft", lines=[(prod, 1, Decimal("1000.00"))])

    # 1. Customer A can view own active subscription
    res = client.get(f"/me/subscriptions/{sub_a.id}", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["id"] == str(sub_a.id)

    # 2. Customer B cannot view Customer A's subscription -> 404 (D21 probing prevention)
    res = client.get(f"/me/subscriptions/{sub_a.id}", headers=headers_b)
    assert res.status_code == 404

    # 3. Customer B cannot view own Draft subscription in portal -> 404 (D21)
    res = client.get(f"/me/subscriptions/{sub_b_draft.id}", headers=headers_b)
    assert res.status_code == 404


def test_subscription_delete_draft_only(client, auth_headers, db):
    headers, _, _ = auth_headers("staff")
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)
    prod, _, _ = create_test_product(db)

    # Draft sub can be deleted
    sub_draft = create_test_subscription(db, cust, plan, term, status="draft", lines=[(prod, 1, Decimal("1000.00"))])
    res = client.delete(f"/subscriptions/{sub_draft.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["action"] == "deleted"

    # Confirmed sub cannot be deleted -> 409
    sub_confirmed = create_test_subscription(db, cust, plan, term, status="confirmed", lines=[(prod, 1, Decimal("1000.00"))])
    res = client.delete(f"/subscriptions/{sub_confirmed.id}", headers=headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "invalid_transition"
