"""
FastAPI HTTP Routers for M3: Billing & Payments.
Exposes both staff/admin router and customer portal router.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core_compat import AppError, AuthUser, require_role, today
from app.database import SessionLocal, get_session
from app.engine import run_billing
from app.models import BillingRun, Invoice, Payment
from app.payments import mock_pay, record_payment
from app.pdf import generate_invoice_pdf
from app.schemas import (
    BillingRunOut,
    BillingRunTriggerInput,
    DiscountCreate,
    DiscountOut,
    DiscountUpdate,
    InvoiceDetail,
    MockPayInput,
    PaymentCreate,
    PaymentOut,
    TaxCreate,
    TaxOut,
    TaxUpdate,
)
from app.service import (
    cancel_invoice_action,
    confirm_invoice_action,
    create_discount,
    create_tax,
    delete_discount,
    delete_tax,
    get_discount,
    get_invoice_detail,
    list_discounts,
    list_invoices,
    list_taxes,
    send_invoice_action,
    update_discount,
    update_tax,
)

router = APIRouter(tags=["billing"])
portal_router = APIRouter(prefix="/me", tags=["billing-portal"])


# Dummy auth dependency for testing/standalone operation
def get_current_user(
    role: str = Query("admin", description="Mock role for standalone testing"),
    customer_id: uuid.UUID | None = Query(None),
) -> AuthUser:
    return AuthUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="admin@brightloop.com" if role == "admin" else "user@example.com",
        role=role,  # type: ignore
        customer_id=customer_id or uuid.UUID("11111111-1111-1111-1111-111111111111"),
        full_name="Mock User",
    )


# -----------------------------------------------------------------------------
# Taxes Endpoints (INV-2)
# -----------------------------------------------------------------------------
@router.get("/taxes", response_model=list[TaxOut], summary="List taxes")
def api_list_taxes(
    active: bool = False,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    return list_taxes(session, active_only=active)


@router.post("/taxes", response_model=TaxOut, status_code=201, summary="Create tax")
def api_create_tax(
    data: TaxCreate,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    res = create_tax(session, data)
    session.commit()
    return res


@router.patch("/taxes/{tax_id}", response_model=TaxOut, summary="Update tax")
def api_update_tax(
    tax_id: uuid.UUID,
    data: TaxUpdate,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    res = update_tax(session, tax_id, data)
    session.commit()
    return res


@router.delete("/taxes/{tax_id}", status_code=204, summary="Delete or deactivate tax")
def api_delete_tax(
    tax_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    delete_tax(session, tax_id)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Discounts Endpoints (DISC-1/2/3)
# -----------------------------------------------------------------------------
@router.get("/discounts", response_model=list[DiscountOut], summary="List discounts")
def api_list_discounts(
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    return list_discounts(session)


@router.get(
    "/discounts/{discount_id}", response_model=DiscountOut, summary="Get discount"
)
def api_get_discount(
    discount_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    return get_discount(session, discount_id)


@router.post(
    "/discounts", response_model=DiscountOut, status_code=201, summary="Create discount"
)
def api_create_discount(
    data: DiscountCreate,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    res = create_discount(session, data)
    session.commit()
    return res


@router.patch(
    "/discounts/{discount_id}", response_model=DiscountOut, summary="Update discount"
)
def api_update_discount(
    discount_id: uuid.UUID,
    data: DiscountUpdate,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    res = update_discount(session, discount_id, data)
    session.commit()
    return res


@router.delete("/discounts/{discount_id}", status_code=204, summary="Delete discount")
def api_delete_discount(
    discount_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin")(user)
    delete_discount(session, discount_id)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Invoices Endpoints (INV-1..5, PAY-3)
# -----------------------------------------------------------------------------
@router.get("/invoices", response_model=dict[str, Any], summary="List invoices")
def api_list_invoices(
    status: str | None = None,
    payment_filter: str | None = None,
    customer_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    items, total = list_invoices(
        session,
        user=user,
        status=status,
        payment_filter=payment_filter,
        customer_id=customer_id,
        subscription_id=subscription_id,
        date_from=date_from,
        date_to=date_to,
        q=q,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/invoices/{invoice_id}", response_model=InvoiceDetail, summary="Get invoice detail"
)
def api_get_invoice(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    return get_invoice_detail(session, invoice_id, user)


@router.post(
    "/invoices/{invoice_id}/confirm",
    response_model=InvoiceDetail,
    summary="Confirm invoice",
)
def api_confirm_invoice(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    res = confirm_invoice_action(session, invoice_id, user)
    session.commit()
    return res


@router.post(
    "/invoices/{invoice_id}/cancel",
    response_model=InvoiceDetail,
    summary="Cancel invoice",
)
def api_cancel_invoice(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    res = cancel_invoice_action(session, invoice_id, user)
    session.commit()
    return res


@router.post(
    "/invoices/{invoice_id}/send",
    response_model=InvoiceDetail,
    summary="Send invoice email",
)
def api_send_invoice(
    invoice_id: uuid.UUID,
    email: str = "customer@example.com",
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    res = send_invoice_action(session, invoice_id, user, email=email)
    session.commit()
    return res


@router.get("/invoices/{invoice_id}/pdf", summary="Download invoice PDF")
def api_invoice_pdf(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    inv_detail = get_invoice_detail(session, invoice_id, user)
    inv = session.get(Invoice, invoice_id)
    pdf_bytes = generate_invoice_pdf(inv)  # type: ignore
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{inv.number}.pdf"'},  # type: ignore
    )


# -----------------------------------------------------------------------------
# Billing Run Endpoints (INV-5)
# -----------------------------------------------------------------------------
@router.post("/billing/run", status_code=202, summary="Trigger billing run")
def api_trigger_billing_run(
    data: BillingRunTriggerInput | None = None,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    as_of = data.as_of if data and data.as_of else today()
    run_id = run_billing(SessionLocal, as_of=as_of, triggered_by=user.id)
    return {"billing_run_id": str(run_id), "status": "running"}


@router.get("/billing/runs", response_model=dict[str, Any], summary="List billing runs")
def api_list_billing_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    stmt = select(BillingRun).order_by(BillingRun.started_at.desc())
    count_stmt = select(func.count(BillingRun.id))
    total = session.scalar(count_stmt) or 0

    runs = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    items = [BillingRunOut.model_validate(r).model_dump() for r in runs]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/billing/runs/{run_id}", response_model=BillingRunOut, summary="Get billing run"
)
def api_get_billing_run(
    run_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    run_obj = session.get(BillingRun, run_id)
    if not run_obj:
        raise AppError("not_found", "Billing run not found", status=404)
    return BillingRunOut.model_validate(run_obj)


# -----------------------------------------------------------------------------
# Payments Endpoints (PAY-1, PAY-2)
# -----------------------------------------------------------------------------
@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=PaymentOut,
    status_code=201,
    summary="Record payment",
)
def api_record_payment(
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    payment = record_payment(session, invoice_id, data, user)
    session.commit()
    return PaymentOut.model_validate(payment)


@router.get("/payments", response_model=list[PaymentOut], summary="List payments")
def api_list_payments(
    invoice_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    require_role("admin", "staff")(user)
    stmt = select(Payment)
    if invoice_id:
        stmt = stmt.where(Payment.invoice_id == invoice_id)
    if customer_id:
        stmt = stmt.where(Payment.customer_id == customer_id)

    payments = session.scalars(stmt.order_by(Payment.paid_on.desc())).all()
    return [PaymentOut.model_validate(p) for p in payments]


# -----------------------------------------------------------------------------
# Customer Portal Endpoints (/me/...)
# -----------------------------------------------------------------------------
@portal_router.get(
    "/invoices", response_model=dict[str, Any], summary="Portal: List own invoices"
)
def portal_list_invoices(
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    items, total = list_invoices(session, user=user)
    return {"items": [i.model_dump() for i in items], "total": total}


@portal_router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceDetail,
    summary="Portal: View invoice detail",
)
def portal_get_invoice(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    return get_invoice_detail(session, invoice_id, user)


@portal_router.get("/invoices/{invoice_id}/pdf", summary="Portal: Download invoice PDF")
def portal_invoice_pdf(
    invoice_id: uuid.UUID,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    inv_detail = get_invoice_detail(session, invoice_id, user)
    inv = session.get(Invoice, invoice_id)
    pdf_bytes = generate_invoice_pdf(inv)  # type: ignore
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{inv.number}.pdf"'},  # type: ignore
    )


@portal_router.post(
    "/invoices/{invoice_id}/pay",
    response_model=PaymentOut,
    summary="Portal: Mock online payment",
)
def portal_pay_invoice(
    invoice_id: uuid.UUID,
    data: MockPayInput | None = None,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    amt = data.amount if data else None
    payment = mock_pay(session, invoice_id, user, amount=amt)
    session.commit()
    return PaymentOut.model_validate(payment)


@portal_router.get(
    "/payments", response_model=list[PaymentOut], summary="Portal: List own payments"
)
def portal_list_payments(
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
):
    stmt = (
        select(Payment)
        .where(Payment.customer_id == user.customer_id)
        .order_by(Payment.paid_on.desc())
    )
    payments = session.scalars(stmt).all()
    return [PaymentOut.model_validate(p) for p in payments]
