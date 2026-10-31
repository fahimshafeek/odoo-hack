"""
Payment processing logic for M3 (PAY-1, PAY-2, D27).
Atomic concurrency-safe implementation for both PostgreSQL and SQLite.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import case, update
from sqlalchemy.orm import Session

from app.core_compat import (
    AppError,
    AuthUser,
    assert_customer_owns,
    invalidate,
    today,
)
from app.models import Invoice, Payment
from app.schemas import PaymentCreate


def record_payment(
    session: Session,
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    user: AuthUser,
) -> Payment:
    """
    Records a payment against a Confirmed invoice (PAY-1).
    Atomic update pattern:
      - Validates amount > 0 and paid_on not in future
      - Atomically updates amount_paid and status where balance >= amount
      - If rowcount == 0, evaluates reason (not found, unconfirmed, or overpayment)
      - Records payment row
      - Invalidates reports cache
    """
    payment_date = data.paid_on or today()
    if payment_date > today():
        raise AppError(
            "validation_error",
            "Payment date cannot be in the future",
            status=422,
            fields={"paid_on": "Cannot be future date"},
        )

    # Atomic check-and-update
    stmt = (
        update(Invoice)
        .where(
            Invoice.id == invoice_id,
            Invoice.status == "confirmed",
            (Invoice.total - Invoice.amount_paid) >= data.amount,
        )
        .values(
            amount_paid=Invoice.amount_paid + data.amount,
            status=case(
                (Invoice.amount_paid + data.amount >= Invoice.total, "paid"),
                else_=Invoice.status,
            ),
        )
    )
    result = session.execute(stmt)

    if result.rowcount == 0:
        inv_check = session.get(Invoice, invoice_id)
        if not inv_check:
            raise AppError("not_found", "Invoice not found", status=404)
        if inv_check.status != "confirmed":
            raise AppError(
                "invoice_not_payable",
                f"Cannot record payment on invoice in '{inv_check.status}' status",
                status=409,
            )
        balance = inv_check.total - inv_check.amount_paid
        if data.amount > balance:
            raise AppError(
                "overpayment",
                f"Payment amount {data.amount} exceeds remaining balance {balance}",
                status=422,
                fields={"amount": "Amount exceeds balance"},
            )
        raise AppError("conflict", "Concurrent payment collision", status=409)

    invoice = session.get(Invoice, invoice_id)

    payment = Payment(
        invoice_id=invoice.id,  # type: ignore
        customer_id=invoice.customer_id,  # type: ignore
        method=data.method,
        amount=data.amount,
        paid_on=payment_date,
        note=data.note,
        recorded_by=user.id,
    )
    session.add(payment)
    session.flush()

    invalidate("reports")
    return payment


def mock_pay(
    session: Session,
    invoice_id: uuid.UUID,
    user: AuthUser,
    amount: Decimal | None = None,
) -> Payment:
    """
    Customer portal self-service mock payment (D27).
    """
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise AppError("not_found", "Invoice not found", status=404)

    assert_customer_owns(user, invoice.customer_id)

    if invoice.status != "confirmed":
        raise AppError("invoice_not_payable", "Invoice is not payable", status=409)

    balance = invoice.total - invoice.amount_paid
    pay_amount = amount if amount is not None else balance

    pay_data = PaymentCreate(
        method="online",
        amount=pay_amount,
        paid_on=today(),
        note="Mock online payment",
    )
    return record_payment(session, invoice.id, pay_data, user)
