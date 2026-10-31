"""
Service layer for M3: Taxes, Discounts, Invoices, and Billing Runs.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.deps import AuthUser, assert_customer_owns
from app.core.clock import today
from app.billing.discounts import get_editable_fields
from app.billing.emailing import send_invoice_email
from app.billing.models import (
    Discount,
    DiscountTarget,
    Invoice,
    InvoiceLine,
    Tax,
)
from app.billing.schemas import (
    CustomerRef,
    DiscountCreate,
    DiscountOut,
    DiscountTargetOut,
    DiscountUpdate,
    InvoiceDetail,
    InvoiceLineOut,
    InvoiceListItem,
    PaymentOut,
    SubscriptionRef,
    TaxCreate,
    TaxOut,
    TaxUpdate,
)
from app.billing.state import (
    allowed_actions,
    cancel_invoice,
    confirm_invoice,
    derive_payment_state,
)


# -----------------------------------------------------------------------------
# Taxes Service (INV-2)
# -----------------------------------------------------------------------------
def list_taxes(session: Session, active_only: bool = False) -> list[TaxOut]:
    stmt = select(Tax)
    if active_only:
        stmt = stmt.where(Tax.is_active == True)
    taxes = session.scalars(stmt.order_by(Tax.name)).all()
    return [TaxOut.model_validate(t) for t in taxes]


def create_tax(session: Session, data: TaxCreate) -> TaxOut:
    existing = session.scalar(select(Tax).where(Tax.name == data.name))
    if existing:
        raise AppError(
            "conflict", f"Tax with name '{data.name}' already exists", status=409
        )

    tax = Tax(
        name=data.name,
        rate_percent=data.rate_percent,
        is_active=data.is_active,
    )
    session.add(tax)
    session.flush()
    return TaxOut.model_validate(tax)


def update_tax(session: Session, tax_id: uuid.UUID, data: TaxUpdate) -> TaxOut:
    tax = session.get(Tax, tax_id)
    if not tax:
        raise AppError("not_found", "Tax not found", status=404)

    if data.name is not None and data.name != tax.name:
        existing = session.scalar(select(Tax).where(Tax.name == data.name))
        if existing:
            raise AppError(
                "conflict", f"Tax with name '{data.name}' already exists", status=409
            )
        tax.name = data.name

    if data.rate_percent is not None:
        tax.rate_percent = data.rate_percent
    if data.is_active is not None:
        tax.is_active = data.is_active

    session.flush()
    return TaxOut.model_validate(tax)


def delete_tax(session: Session, tax_id: uuid.UUID) -> None:
    tax = session.get(Tax, tax_id)
    if not tax:
        raise AppError("not_found", "Tax not found", status=404)

    # Check if referenced by invoice lines or plan fee
    ref_count = session.scalar(
        select(func.count(InvoiceLine.id)).where(
            InvoiceLine.tax_rate == tax.rate_percent
        )
    )
    if ref_count and ref_count > 0:
        # Soft-delete (deactivate)
        tax.is_active = False
    else:
        session.delete(tax)
    session.flush()


# -----------------------------------------------------------------------------
# Discounts Service (DISC-1/2/3, D19)
# -----------------------------------------------------------------------------
def _discount_to_out(discount: Discount) -> DiscountOut:
    targets_out = [
        DiscountTargetOut(
            product_id=t.product_id,
            subscription_id=t.subscription_id,
            label=f"Product {t.product_id}"
            if t.product_id
            else f"Subscription {t.subscription_id}",
        )
        for t in discount.targets
    ]
    return DiscountOut(
        id=discount.id,
        name=discount.name,
        type=discount.type,
        value=discount.value,
        scope=discount.scope,
        min_purchase=discount.min_purchase,
        min_quantity=discount.min_quantity,
        start_date=discount.start_date,
        end_date=discount.end_date,
        usage_limit=discount.usage_limit,
        used_count=discount.used_count,
        is_active=discount.is_active,
        targets=targets_out,
        editable_fields=get_editable_fields(discount),
    )


def list_discounts(session: Session) -> list[DiscountOut]:
    discounts = session.scalars(select(Discount).order_by(Discount.name)).all()
    return [_discount_to_out(d) for d in discounts]


def get_discount(session: Session, discount_id: uuid.UUID) -> DiscountOut:
    discount = session.get(Discount, discount_id)
    if not discount:
        raise AppError("not_found", "Discount not found", status=404)
    return _discount_to_out(discount)


def create_discount(session: Session, data: DiscountCreate) -> DiscountOut:
    discount = Discount(
        name=data.name,
        type=data.type,
        value=data.value,
        scope=data.scope,
        min_purchase=data.min_purchase,
        min_quantity=data.min_quantity,
        start_date=data.start_date,
        end_date=data.end_date,
        usage_limit=data.usage_limit,
        is_active=data.is_active,
    )
    session.add(discount)
    session.flush()

    for t in data.targets:
        target = DiscountTarget(
            discount_id=discount.id,
            product_id=t.product_id,
            subscription_id=t.subscription_id,
        )
        session.add(target)

    session.flush()
    return _discount_to_out(discount)


def update_discount(
    session: Session, discount_id: uuid.UUID, data: DiscountUpdate
) -> DiscountOut:
    discount = session.get(Discount, discount_id)
    if not discount:
        raise AppError("not_found", "Discount not found", status=404)

    # D19 Edit-Lock: once used_count > 0, cannot change type, value, scope, or targets
    if discount.used_count > 0:
        if data.type is not None and data.type != discount.type:
            raise AppError(
                "conflict",
                "Cannot modify 'type' after discount has been used",
                status=409,
            )
        if data.value is not None and data.value != discount.value:
            raise AppError(
                "conflict",
                "Cannot modify 'value' after discount has been used",
                status=409,
            )
        if data.scope is not None and data.scope != discount.scope:
            raise AppError(
                "conflict",
                "Cannot modify 'scope' after discount has been used",
                status=409,
            )
        if data.targets is not None:
            raise AppError(
                "conflict",
                "Cannot modify 'targets' after discount has been used",
                status=409,
            )
        if data.usage_limit is not None and data.usage_limit < discount.used_count:
            raise AppError(
                "validation_error",
                f"usage_limit cannot be less than already used_count ({discount.used_count})",
                status=422,
            )

    if data.name is not None:
        discount.name = data.name
    if data.type is not None:
        discount.type = data.type
    if data.value is not None:
        discount.value = data.value
    if data.scope is not None:
        discount.scope = data.scope
    if data.min_purchase is not None:
        discount.min_purchase = data.min_purchase
    if data.min_quantity is not None:
        discount.min_quantity = data.min_quantity
    if data.start_date is not None:
        discount.start_date = data.start_date
    if data.end_date is not None:
        discount.end_date = data.end_date
    if data.usage_limit is not None:
        discount.usage_limit = data.usage_limit
    if data.is_active is not None:
        discount.is_active = data.is_active

    if data.targets is not None and discount.used_count == 0:
        session.execute(
            delete(DiscountTarget).where(DiscountTarget.discount_id == discount.id)
        )
        for t in data.targets:
            target = DiscountTarget(
                discount_id=discount.id,
                product_id=t.product_id,
                subscription_id=t.subscription_id,
            )
            session.add(target)

    session.flush()
    return _discount_to_out(discount)


def delete_discount(session: Session, discount_id: uuid.UUID) -> None:
    discount = session.get(Discount, discount_id)
    if not discount:
        raise AppError("not_found", "Discount not found", status=404)

    if discount.used_count > 0:
        discount.is_active = False
    else:
        session.delete(discount)
    session.flush()


# -----------------------------------------------------------------------------
# Invoices Service (INV-1..5, PAY-3)
# -----------------------------------------------------------------------------
def _build_invoice_list_item(inv: Invoice, curr_date: date) -> InvoiceListItem:
    p_state = derive_payment_state(inv, curr_date)
    balance = inv.total - inv.amount_paid
    is_overdue = (
        (inv.status == "confirmed") and (balance > 0) and (inv.due_date < curr_date)
    )
    days_overdue = (curr_date - inv.due_date).days if is_overdue else 0

    return InvoiceListItem(
        id=inv.id,
        number=inv.number,
        status=inv.status,
        payment_state=p_state,
        is_overdue=is_overdue,
        days_overdue=days_overdue,
        customer=CustomerRef(
            id=inv.customer_id, name="Acme Corp", email="billing@acme.com"
        ),
        subscription=SubscriptionRef(
            id=inv.subscription_id, number=f"SUB-{str(inv.subscription_id)[:8]}"
        ),
        period_start=inv.period_start,
        period_end=inv.period_end,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        total=inv.total,
        amount_paid=inv.amount_paid,
        balance=balance,
    )


def list_invoices(
    session: Session,
    user: AuthUser,
    status: str | None = None,
    payment_filter: str | None = None,
    customer_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[InvoiceListItem], int]:
    curr_date = today()
    stmt = select(Invoice)

    # Customer scoping (D21)
    if user.role == "customer":
        stmt = stmt.where(
            Invoice.customer_id == user.customer_id,
            Invoice.status.in_(["confirmed", "paid"]),
        )
    else:
        if customer_id:
            stmt = stmt.where(Invoice.customer_id == customer_id)

    if subscription_id:
        stmt = stmt.where(Invoice.subscription_id == subscription_id)

    if status:
        stmt = stmt.where(Invoice.status == status)

    if date_from:
        stmt = stmt.where(Invoice.issue_date >= date_from)
    if date_to:
        stmt = stmt.where(Invoice.issue_date <= date_to)

    if q:
        stmt = stmt.where(Invoice.number.ilike(f"%{q}%"))

    # Payment filter: paid | outstanding | overdue
    if payment_filter == "paid":
        stmt = stmt.where(Invoice.status == "paid")
    elif payment_filter == "outstanding":
        stmt = stmt.where(
            Invoice.status == "confirmed",
            (Invoice.total - Invoice.amount_paid) > Decimal("0.00"),
        )
    elif payment_filter == "overdue":
        stmt = stmt.where(
            Invoice.status == "confirmed",
            (Invoice.total - Invoice.amount_paid) > Decimal("0.00"),
            Invoice.due_date < curr_date,
        )

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = session.scalar(count_stmt) or 0

    # Paginate and order by -issue_date, -created_at
    stmt = stmt.order_by(Invoice.issue_date.desc(), Invoice.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    invoices = session.scalars(stmt).all()
    items = [_build_invoice_list_item(inv, curr_date) for inv in invoices]
    return items, total_count


def get_invoice_detail(
    session: Session, invoice_id: uuid.UUID, user: AuthUser
) -> InvoiceDetail:
    inv = session.get(Invoice, invoice_id)
    if not inv:
        raise AppError("not_found", "Invoice not found", status=404)

    # Customer visibility guard (D21)
    if user.role == "customer":
        assert_customer_owns(user, inv.customer_id)
        if inv.status not in ("confirmed", "paid"):
            raise AppError("not_found", "Invoice not found", status=404)

    curr_date = today()
    base_item = _build_invoice_list_item(inv, curr_date)

    lines_out = [
        InvoiceLineOut(
            id=line.id,
            line_type=line.line_type,
            description=line.description,
            product_id=line.product_id,
            quantity=line.quantity,
            unit_price=line.unit_price,
            gross_amount=line.gross_amount,
            discount_amount=line.discount_amount,
            discount={"id": str(line.discount_id)} if line.discount_id else None,
            tax_rate=line.tax_rate,
            tax_amount=line.tax_amount,
            line_total=line.line_total,
            position=line.position,
        )
        for line in inv.lines
    ]

    payments_out = [
        PaymentOut(
            id=p.id,
            invoice_id=p.invoice_id,
            customer_id=p.customer_id,
            method=p.method,
            amount=p.amount,
            paid_on=p.paid_on,
            note=p.note,
            recorded_by=p.recorded_by,
            created_at=p.created_at,
        )
        for p in inv.payments
    ]

    return InvoiceDetail(
        **base_item.model_dump(),
        subtotal=inv.subtotal,
        discount_total=inv.discount_total,
        tax_total=inv.tax_total,
        confirmed_at=inv.confirmed_at,
        sent_at=inv.sent_at,
        cancelled_at=inv.cancelled_at,
        customer_billing={
            "billing_address": "123 Main St, Bengaluru",
            "tax_id": "GSTIN29AAAAA0000A1Z5",
            "phone": "+919876543210",
        },
        lines=lines_out,
        payments=payments_out,
        allowed_actions=allowed_actions(inv, user),
    )


def confirm_invoice_action(
    session: Session, invoice_id: uuid.UUID, user: AuthUser
) -> InvoiceDetail:
    inv = session.get(Invoice, invoice_id)
    if not inv:
        raise AppError("not_found", "Invoice not found", status=404)
    confirm_invoice(session, inv, user)
    return get_invoice_detail(session, invoice_id, user)


def cancel_invoice_action(
    session: Session, invoice_id: uuid.UUID, user: AuthUser
) -> InvoiceDetail:
    inv = session.get(Invoice, invoice_id)
    if not inv:
        raise AppError("not_found", "Invoice not found", status=404)
    cancel_invoice(session, inv, user)
    return get_invoice_detail(session, invoice_id, user)


def send_invoice_action(
    session: Session,
    invoice_id: uuid.UUID,
    user: AuthUser,
    email: str = "customer@example.com",
) -> InvoiceDetail:
    inv = session.get(Invoice, invoice_id)
    if not inv:
        raise AppError("not_found", "Invoice not found", status=404)
    if inv.status not in ("confirmed", "paid"):
        raise AppError(
            "invalid_transition",
            f"Cannot send invoice in '{inv.status}' status",
            status=409,
        )

    send_invoice_email(inv, recipient_email=email)
    session.flush()
    return get_invoice_detail(session, invoice_id, user)
