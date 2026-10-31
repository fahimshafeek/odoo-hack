import uuid
from decimal import Decimal
import pytest
from app.catalog.models import Product, Plan, PaymentTerm, QuotationTemplate
from tests.factories import (
    create_test_tax,
    create_test_product,
    create_test_plan,
    create_test_payment_term,
    create_test_customer,
    create_test_subscription,
)


def test_product_crud_and_soft_warning(client, auth_headers, db):
    headers, _, _ = auth_headers("admin")
    tax = create_test_tax(db)

    # 1. Create product where cost_price > sales_price -> should have soft warning
    payload = {
        "name": "Cloud Server Pro",
        "type": "infrastructure",
        "sales_price": "1000.00",
        "cost_price": "1200.00",
        "notes": "Dedicated compute node",
        "tax_id": str(tax.id),
        "is_active": True,
    }
    res = client.post("/products", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Cloud Server Pro"
    assert data["sales_price"] == "1000.00"
    assert "cost_price_exceeds_sales_price" in data["warnings"]
    prod_id = data["id"]

    # 2. Add attributes & values
    attr_payload = {
        "name": "RAM",
        "values": [
            {"name": "16GB", "extra_price": "0.00"},
            {"name": "32GB", "extra_price": "500.00"},
        ],
    }
    res = client.post(f"/products/{prod_id}/attributes", json=attr_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert len(data["attributes"]) == 1
    assert data["attributes"][0]["name"] == "RAM"
    assert len(data["attributes"][0]["values"]) == 2

    # 3. List products
    res = client.get("/products", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    # 4. Patch product (update sales price so cost <= sales)
    patch_payload = {"sales_price": "1500.00"}
    res = client.patch(f"/products/{prod_id}", json=patch_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["sales_price"] == "1500.00"
    assert "cost_price_exceeds_sales_price" not in res.json()["warnings"]

    # 5. Delete product
    res = client.delete(f"/products/{prod_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["action"] == "deleted"


def test_product_delete_deactivates_when_referenced(client, auth_headers, db):
    headers, _, _ = auth_headers("admin")
    tax = create_test_tax(db)
    prod, _, _ = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)
    term = create_test_payment_term(db)
    cust, _ = create_test_customer(db)

    # Create subscription referencing product
    create_test_subscription(db, cust, plan, term, lines=[(prod, 1, Decimal("1000.00"))])

    # Delete should deactivate instead of hard delete
    res = client.delete(f"/products/{prod.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["action"] == "deactivated"

    # Verify is_active is now False in DB
    refreshed_prod = db.get(Product, prod.id)
    assert refreshed_prod.is_active is False


def test_plans_crud_and_close(client, auth_headers, db):
    headers, _, _ = auth_headers("admin")

    # 1. Create plan
    payload = {
        "name": "Enterprise Yearly",
        "price": "12000.00",
        "billing_period": "yearly",
        "min_quantity": 5,
        "auto_close": True,
        "allow_early_close": True,
        "allow_pause": False,
        "allow_renew": True,
        "is_active": True,
    }
    res = client.post("/plans", json=payload, headers=headers)
    assert res.status_code == 201
    plan_id = res.json()["id"]
    assert res.json()["allow_pause"] is False
    assert res.json()["min_quantity"] == 5

    # 2. Get plan
    res = client.get(f"/plans/{plan_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Enterprise Yearly"

    # 3. Close plan (POST /plans/{id}/close)
    res = client.post(f"/plans/{plan_id}/close", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_payment_terms_crud(client, auth_headers):
    headers, _, _ = auth_headers("admin")

    # Create
    res = client.post("/payment-terms", json={"name": "Net 45", "due_days": 45}, headers=headers)
    assert res.status_code == 201
    term_id = res.json()["id"]
    assert res.json()["due_days"] == 45

    # Update
    res = client.patch(f"/payment-terms/{term_id}", json={"due_days": 60}, headers=headers)
    assert res.status_code == 200
    assert res.json()["due_days"] == 60

    # Delete
    res = client.delete(f"/payment-terms/{term_id}", headers=headers)
    assert res.status_code == 200


def test_quotation_template_crud(client, auth_headers, db):
    headers, _, _ = auth_headers("admin")
    tax = create_test_tax(db)
    prod, attr, val = create_test_product(db, tax_id=tax.id)
    plan = create_test_plan(db)

    payload = {
        "name": "Standard Onboarding Quote",
        "plan_id": str(plan.id),
        "validity_days": 15,
        "lines": [
            {
                "product_id": str(prod.id),
                "quantity": 2,
                "variant_value_ids": [str(val.id)],
                "tax_id": str(tax.id),
            }
        ],
    }
    res = client.post("/quotation-templates", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Standard Onboarding Quote"
    assert data["validity_days"] == 15
    assert len(data["lines"]) == 1
    # 1000 base + 560 Odoo = 1560.00 unit price
    assert data["lines"][0]["unit_price"] == "1560.00"
    assert data["lines"][0]["amount"] == "3120.00"
    tpl_id = data["id"]

    # Get
    res = client.get(f"/quotation-templates/{tpl_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == tpl_id


@pytest.mark.parametrize(
    "endpoint, payload, expected_status",
    [
        ("/products", {"name": "", "sales_price": "100.00", "cost_price": "50.00"}, 422),  # empty name
        ("/products", {"name": "Test", "sales_price": "-10.00", "cost_price": "50.00"}, 422),  # negative money
        ("/plans", {"name": "Test", "price": "100.00", "billing_period": "invalid_period"}, 422),  # invalid enum
        ("/plans", {"name": "Test", "price": "100.00", "billing_period": "monthly", "min_quantity": 0}, 422),  # min qty < 1
        ("/payment-terms", {"name": "Test", "due_days": 400}, 422),  # due days > 365
        ("/quotation-templates", {"name": "Test", "plan_id": str(uuid.uuid4()), "validity_days": 0}, 422),  # validity < 1
    ],
)
def test_invalid_input_rejected_with_422(client, auth_headers, endpoint, payload, expected_status):
    headers, _, _ = auth_headers("admin")
    res = client.post(endpoint, json=payload, headers=headers)
    assert res.status_code == expected_status
    assert res.json()["error"]["code"] == "validation_error"
