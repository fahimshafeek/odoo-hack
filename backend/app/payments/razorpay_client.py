"""
Razorpay Payment Gateway integration client for M3.
Handles Razorpay Orders API, HMAC-SHA256 signature verification, and webhooks.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from app.core.errors import AppError

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


def get_razorpay_key_id() -> str:
    return RAZORPAY_KEY_ID


def inr_to_paise(amount: Decimal) -> int:
    """Converts Decimal INR (e.g. 1500.50) to integer paise (150050)."""
    return int(amount * 100)


def create_razorpay_order(
    amount: Decimal,
    invoice_number: str,
    invoice_id: uuid.UUID,
    customer_id: uuid.UUID,
    currency: str = "INR",
) -> dict[str, Any]:
    """
    Creates an order on Razorpay for the given invoice.
    Uses real Razorpay REST API when real credentials are configured,
    or generates a compliant test order ID for local/offline testing.
    """
    amount_paise = inr_to_paise(amount)
    key_id = RAZORPAY_KEY_ID
    key_secret = RAZORPAY_KEY_SECRET

    payload = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": invoice_number[:40],
        "notes": {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice_number,
            "customer_id": str(customer_id),
        },
    }

    # If real test/live key configured and not placeholder, call Razorpay API
    is_live_key = (
        key_id.startswith(("rzp_test_", "rzp_live_"))
        and key_id != "rzp_test_placeholder"
    )

    if is_live_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{RAZORPAY_API_BASE}/orders",
                    auth=(key_id, key_secret),
                    json=payload,
                )
                if resp.status_code not in (200, 201):
                    error_data = resp.json().get("error", {})
                    raise AppError(
                        "razorpay_error",
                        f"Razorpay order creation failed: {error_data.get('description', resp.text)}",
                        status=502,
                    )
                data = resp.json()
                return {
                    "id": data["id"],
                    "amount": data["amount"],
                    "currency": data.get("currency", "INR"),
                    "key_id": key_id,
                }
        except httpx.RequestError as exc:
            raise AppError(
                "razorpay_connection_error",
                f"Could not connect to Razorpay API: {exc}",
                status=502,
            ) from exc

    # Offline/Mock test mode order creation
    mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
    return {
        "id": mock_order_id,
        "amount": amount_paise,
        "currency": currency,
        "key_id": key_id,
    }


def create_razorpay_payment_link(
    amount: Decimal,
    invoice_number: str,
    invoice_id: uuid.UUID,
    customer_name: str = "",
    customer_email: str = "",
    customer_contact: str = "",
    callback_url: str = "",
) -> dict[str, Any]:
    """
    Creates a Razorpay Payment Link (hosted rzp.io short URL) via /v1/payment_links.
    Customers can open this URL directly in their browser or mobile to pay via UPI/Card.
    """
    amount_paise = inr_to_paise(amount)
    key_id = RAZORPAY_KEY_ID
    key_secret = RAZORPAY_KEY_SECRET

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": f"Payment for Invoice {invoice_number}",
        "customer": {
            "name": customer_name or "Valued Customer",
            "email": customer_email or "billing@example.com",
            "contact": customer_contact or "+919999999999",
        },
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice_number,
        },
    }
    if callback_url:
        payload["callback_url"] = callback_url
        payload["callback_method"] = "get"

    is_live_key = (
        key_id.startswith(("rzp_test_", "rzp_live_"))
        and key_id != "rzp_test_placeholder"
    )

    if is_live_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{RAZORPAY_API_BASE}/payment_links",
                    auth=(key_id, key_secret),
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {
                        "id": data["id"],
                        "short_url": data.get("short_url", ""),
                        "status": data.get("status", "created"),
                        "amount": data["amount"],
                    }
                error_data = resp.json().get("error", {})
                raise AppError(
                    "razorpay_error",
                    f"Payment link creation failed: {error_data.get('description', resp.text)}",
                    status=502,
                )
        except httpx.RequestError as exc:
            raise AppError(
                "razorpay_connection_error",
                f"Could not connect to Razorpay API: {exc}",
                status=502,
            ) from exc

    # Offline/Mock test mode short url
    link_id = f"plink_{uuid.uuid4().hex[:14]}"
    return {
        "id": link_id,
        "short_url": f"https://rzp.io/rzp/mock_{uuid.uuid4().hex[:8]}",
        "status": "created",
        "amount": amount_paise,
    }


def verify_razorpay_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    secret: str | None = None,
) -> bool:
    """
    Verifies Razorpay's HMAC-SHA256 signature for checkout payments:
    expected_signature = HMAC-SHA256(order_id + "|" + payment_id, secret)
    """
    key_secret = secret or RAZORPAY_KEY_SECRET
    if not key_secret:
        return False

    msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    expected_signature = hmac.new(
        key_secret.encode("utf-8"), msg, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, razorpay_signature)


def generate_test_signature(
    order_id: str, payment_id: str, secret: str | None = None
) -> str:
    """Helper to compute valid HMAC-SHA256 signature for automated tests."""
    key_secret = secret or RAZORPAY_KEY_SECRET
    msg = f"{order_id}|{payment_id}".encode()
    return hmac.new(key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_razorpay_webhook_signature(
    payload_body: bytes,
    signature: str,
    webhook_secret: str | None = None,
) -> bool:
    """Verifies Razorpay webhook signature from X-Razorpay-Signature header."""
    secret = webhook_secret or RAZORPAY_WEBHOOK_SECRET
    if not secret:
        return False

    expected = hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
