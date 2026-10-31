"""
Invoice state machine and action guards for M3 (INV-4, D20).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core_compat import AppError, AuthUser, now, today
from app.discounts import release_discount_usage
from app.models import Invoice


def derive_payment_state(invoice: Invoice, today_val: date | None = None) -> str:
    """
    Computes derived payment_state:
      Draft / Cancelled -> 'not_applicable'
      Paid -> 'paid'
      Confirmed -> 'overdue' if due_date < today else 'partially_paid' if amount_paid > 0 else 'unpaid'
    """
    if invoice.status in ("draft", "cancelled"):
        return "not_applicable"
    if invoice.status == "paid":
        return "paid"

    curr_date = today_val or today()
    balance = invoice.total - invoice.amount_paid

    if invoice.status == "confirmed":
        if balance > 0 and invoice.due_date < curr_date:
            return "overdue"
        if invoice.amount_paid > Decimal("0.00"):
            return "partially_paid"
        return "unpaid"

    return "unpaid"


def allowed_actions(invoice: Invoice, user: AuthUser) -> list[str]:
    """
    Returns allowed action names for the given invoice and user role.
    """
    if user.role == "customer":
        actions = []
        if invoice.status in ("confirmed", "paid"):
            actions.append("print")
        if invoice.status == "confirmed" and (
            invoice.total - invoice.amount_paid
        ) > Decimal("0.00"):
            actions.append("pay")
        return actions

    # Staff / Admin
    actions: list[str] = []
    if invoice.status == "draft":
        actions.extend(["confirm", "cancel"])
    elif invoice.status == "confirmed":
        if invoice.amount_paid == Decimal("0.00"):
            actions.append("cancel")
        actions.extend(["send", "print"])
        if (invoice.total - invoice.amount_paid) > Decimal("0.00"):
            actions.append("record_payment")
    elif invoice.status == "paid":
        actions.extend(["send", "print"])

    return actions


def confirm_invoice(session: Session, invoice: Invoice, user: AuthUser) -> Invoice:
    """
    Transitions invoice: Draft -> Confirmed (sets confirmed_at).
    If total == 0, immediately transitions to Paid (D20).
    """
    if invoice.status != "draft":
        raise AppError(
            "invalid_transition",
            f"Cannot confirm invoice in '{invoice.status}' status",
            status=409,
        )

    invoice.status = "confirmed"
    invoice.confirmed_at = now()

    # D20 zero-total check
    if invoice.total == Decimal("0.00"):
        invoice.status = "paid"

    session.flush()
    return invoice


def cancel_invoice(session: Session, invoice: Invoice, user: AuthUser) -> Invoice:
    """
    Transitions invoice to Cancelled.
      - Draft -> Cancelled: releases discount usage (D20), deletes redemptions.
      - Confirmed -> Cancelled: allowed only if amount_paid == 0; discount usage is NOT released.
    """
    if invoice.status == "cancelled":
        raise AppError("invalid_transition", "Invoice is already cancelled", status=409)

    if invoice.status == "draft":
        # Release discount redemptions
        for red in list(invoice.redemptions):
            release_discount_usage(session, red.discount_id)
            session.delete(red)
    elif invoice.status == "confirmed":
        if invoice.amount_paid > Decimal("0.00"):
            raise AppError(
                "invalid_transition",
                "Cannot cancel a confirmed invoice with recorded payments",
                status=409,
            )
    else:
        raise AppError(
            "invalid_transition",
            f"Cannot cancel invoice in '{invoice.status}' status",
            status=409,
        )

    invoice.status = "cancelled"
    invoice.cancelled_at = now()
    session.flush()
    return invoice
