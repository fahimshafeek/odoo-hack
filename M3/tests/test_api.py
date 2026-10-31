"""
Comprehensive HTTP API endpoint tests for M3.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from app.core_compat import today
from app.models import Invoice


def test_api_taxes_crud(client):
    # 1. Create tax
    create_res = client.post(
        "/taxes",
        json={"name": "VAT 15%", "rate_percent": "15.00", "is_active": True},
        params={"role": "admin"},
    )
    assert create_res.status_code == 201
    tax_data = create_res.json()
    tax_id = tax_data["id"]
    assert tax_data["name"] == "VAT 15%"
    assert tax_data["rate_percent"] == "15.00"

    # 2. List taxes
    list_res = client.get("/taxes", params={"role": "staff"})
    assert list_res.status_code == 200
    assert any(t["id"] == tax_id for t in list_res.json())

    # 3. Staff cannot create -> 403
    forbidden_res = client.post(
        "/taxes",
        json={"name": "Tax Staff", "rate_percent": "5.00"},
        params={"role": "staff"},
    )
    assert forbidden_res.status_code == 403


def test_api_discounts_crud(client):
    curr_date = today()
    create_res = client.post(
        "/discounts",
        json={
            "name": "Promo 25",
            "type": "percent",
            "value": "25.00",
            "scope": "subscription",
            "start_date": str(curr_date),
            "end_date": str(curr_date + timedelta(days=30)),
            "usage_limit": 10,
        },
        params={"role": "admin"},
    )
    assert create_res.status_code == 201
    disc_id = create_res.json()["id"]

    # Read discounts
    get_res = client.get(f"/discounts/{disc_id}", params={"role": "staff"})
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Promo 25"


def test_api_invoices_actions_and_payments(client, db):
    curr_date = today()
    cust_id = uuid.uuid4()

    # Create confirmed invoice in db
    inv = Invoice(
        number="INV-2026-APITEST",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    # 1. Get detail
    det_res = client.get(f"/invoices/{inv.id}", params={"role": "admin"})
    assert det_res.status_code == 200
    assert det_res.json()["number"] == "INV-2026-APITEST"
    assert "record_payment" in det_res.json()["allowed_actions"]

    # 2. Record payment
    pay_res = client.post(
        f"/invoices/{inv.id}/payments",
        json={"method": "upi", "amount": "200.00"},
        params={"role": "admin"},
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["amount"] == "200.00"

    # 3. Check updated balance
    det_res2 = client.get(f"/invoices/{inv.id}", params={"role": "admin"})
    assert det_res2.json()["amount_paid"] == "200.00"
    assert det_res2.json()["balance"] == "300.00"

    # 4. Download PDF
    pdf_res = client.get(f"/invoices/{inv.id}/pdf", params={"role": "admin"})
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")


def test_api_portal_customer_scoping(client, db):
    curr_date = today()
    cust1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    cust2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

    inv1 = Invoice(
        number="INV-2026-CUST1",
        subscription_id=uuid.uuid4(),
        customer_id=cust1,
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("150.00"),
    )
    inv2 = Invoice(
        number="INV-2026-CUST2",
        subscription_id=uuid.uuid4(),
        customer_id=cust2,
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date + timedelta(days=30),
        issue_date=curr_date,
        due_date=curr_date + timedelta(days=15),
        total=Decimal("300.00"),
    )
    db.add_all([inv1, inv2])
    db.commit()

    # Customer 1 lists invoices: only sees inv1
    list_res = client.get(
        "/me/invoices", params={"role": "customer", "customer_id": str(cust1)}
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 1
    assert items[0]["number"] == "INV-2026-CUST1"

    # Customer 1 tries to access Customer 2's invoice -> 404 (not 403, per D21)
    forbidden_res = client.get(
        f"/me/invoices/{inv2.id}",
        params={"role": "customer", "customer_id": str(cust1)},
    )
    assert forbidden_res.status_code == 404
