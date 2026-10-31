"""
Unit and integration tests for Razorpay Payment Gateway integration.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core_compat import today
from app.models import Invoice, Payment
from app.razorpay_client import generate_test_signature


def test_razorpay_order_creation_and_database_persistence(client, db):
    # 1. Setup confirmed invoice
    cust_id = uuid.uuid4()
    inv = Invoice(
        number="INV-RZP-001",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        subtotal=Decimal("1500.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        total=Decimal("1500.00"),
        amount_paid=Decimal("500.00"),  # Balance = 1000.00
    )
    db.add(inv)
    db.commit()

    # 2. Call customer portal to create Razorpay order
    resp = client.post(
        f"/me/invoices/{inv.id}/razorpay/order?customer_id={cust_id}&role=customer"
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["invoice_id"] == str(inv.id)
    assert data["amount"] == 100000  # 1000 INR = 100,000 paise
    assert data["currency"] == "INR"
    assert data["order_id"].startswith("order_")
    assert "key_id" in data

    # 3. Verify DB has razorpay_order_id stored
    db.refresh(inv)
    assert inv.razorpay_order_id == data["order_id"]


def test_razorpay_signature_verification_success(client, db):
    cust_id = uuid.uuid4()
    inv = Invoice(
        number="INV-RZP-002",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        subtotal=Decimal("800.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        total=Decimal("800.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    order_id = "order_test_123456"
    payment_id = "pay_test_987654"
    inv.razorpay_order_id = order_id
    db.commit()

    # Generate valid signature
    valid_signature = generate_test_signature(order_id, payment_id)

    verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": valid_signature,
    }

    resp = client.post(
        f"/me/invoices/{inv.id}/razorpay/verify?customer_id={cust_id}&role=customer",
        json=verify_payload,
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["invoice_status"] == "paid"
    assert res_data["remaining_balance"] == "0.00"

    # Verify payment recorded in DB
    db.refresh(inv)
    assert inv.status == "paid"
    assert inv.amount_paid == Decimal("800.00")

    payment = (
        db.query(Payment).filter_by(invoice_id=inv.id, reference=payment_id).first()
    )
    assert payment is not None
    assert payment.method == "online"
    assert payment.amount == Decimal("800.00")


def test_razorpay_signature_verification_rejection(client, db):
    cust_id = uuid.uuid4()
    inv = Invoice(
        number="INV-RZP-003",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        total=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    bad_payload = {
        "razorpay_order_id": "order_test_999",
        "razorpay_payment_id": "pay_test_999",
        "razorpay_signature": "invalid_forged_signature_12345",
    }

    resp = client.post(
        f"/me/invoices/{inv.id}/razorpay/verify?customer_id={cust_id}&role=customer",
        json=bad_payload,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_signature"

    # Verify invoice was NOT settled
    db.refresh(inv)
    assert inv.status == "confirmed"
    assert inv.amount_paid == Decimal("0.00")


def test_razorpay_duplicate_verification_idempotency(client, db):
    cust_id = uuid.uuid4()
    inv = Invoice(
        number="INV-RZP-004",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        total=Decimal("600.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    order_id = "order_idem_111"
    payment_id = "pay_idem_222"
    valid_sig = generate_test_signature(order_id, payment_id)

    payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": valid_sig,
    }

    # 1. First verification
    resp1 = client.post(
        f"/me/invoices/{inv.id}/razorpay/verify?customer_id={cust_id}&role=customer",
        json=payload,
    )
    assert resp1.status_code == 200

    # 2. Second duplicate verification (e.g. network retry from frontend)
    resp2 = client.post(
        f"/me/invoices/{inv.id}/razorpay/verify?customer_id={cust_id}&role=customer",
        json=payload,
    )
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True

    # Confirm only 1 payment was created
    count = db.query(Payment).filter_by(invoice_id=inv.id, reference=payment_id).count()
    assert count == 1


def test_razorpay_webhook_event_capture(client, db):
    cust_id = uuid.uuid4()
    order_id = "order_hook_333"
    payment_id = "pay_hook_444"

    inv = Invoice(
        number="INV-RZP-005",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        razorpay_order_id=order_id,
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        total=Decimal("750.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 75000,  # 750 INR
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }

    resp = client.post("/razorpay/webhook", json=webhook_payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Verify invoice was updated
    db.refresh(inv)
    assert inv.status == "paid"
    assert inv.amount_paid == Decimal("750.00")


def test_razorpay_payment_link_generation(client, db):
    cust_id = uuid.uuid4()
    inv = Invoice(
        number="INV-RZP-LINK-001",
        subscription_id=uuid.uuid4(),
        customer_id=cust_id,
        status="confirmed",
        period_start=today(),
        period_end=today(),
        issue_date=today(),
        due_date=today(),
        total=Decimal("1200.00"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    db.commit()

    resp = client.post(
        f"/me/invoices/{inv.id}/razorpay/link?customer_id={cust_id}&role=customer"
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["invoice_id"] == str(inv.id)
    assert data["amount"] == 120000  # 1200 INR = 120,000 paise
    assert "short_url" in data
    assert data["short_url"].startswith("https://rzp.io/")
