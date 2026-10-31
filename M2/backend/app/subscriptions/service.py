import uuid
import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.core.clock import today as get_today, now as get_now
from app.core.errors import AppError
from app.core.deps import AuthUser, assert_customer_owns
from app.core.pagination import PageParams, Page, paginate
from app.core.money import to_decimal, q2, tax_amount
from app.core.numbering import next_number
from app.catalog.models import (
    Product,
    ProductAttribute,
    Plan,
    PaymentTerm,
    QuotationTemplate,
    TemplateLine,
    Tax,
)
from app.core.models import Customer, User
from app.subscriptions.models import (
    Subscription,
    SubscriptionLine,
    SubscriptionHistory,
)
from app.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    FromTemplateCreate,
    SubscriptionListItem,
    SubscriptionDetail,
    SubscriptionLineOut,
    PlanFeeLine,
    TotalsOut,
    HistoryItem,
    PricePreviewInput,
    PricePreviewOut,
    PricePreviewLine,
    PaymentTermRef,
)
from app.catalog.schemas import CustomerRef, PlanRef, ProductRef, TaxRef, UserRef
from app.subscriptions.pricing import resolve_variant, unit_price, line_amount
from app.subscriptions.state import allowed_actions


# ==========================================
# PRICING PREVIEW
# ==========================================

def preview_pricing(session, data: PricePreviewInput) -> PricePreviewOut:
    plan = None
    plan_fee = None
    plan_fee_amount = Decimal("0.00")
    plan_fee_tax = Decimal("0.00")

    if data.plan_id:
        plan = session.get(Plan, data.plan_id)
        if not plan:
            raise AppError("not_found", f"Plan {data.plan_id} not found", 404)
        if plan.tax_id:
            ptax = session.get(Tax, plan.tax_id)
            ptax_rate = to_decimal(ptax.rate_percent) if ptax else Decimal("0.00")
        else:
            ptax_rate = Decimal("0.00")

        pf_amt = to_decimal(plan.price)
        pf_tax = tax_amount(pf_amt, ptax_rate)
        plan_fee_amount = pf_amt
        plan_fee_tax = pf_tax
        plan_fee = PlanFeeLine(
            amount=pf_amt,
            tax_rate=ptax_rate,
            tax_amount=pf_tax,
            total=q2(pf_amt + pf_tax),
        )

    out_lines = []
    lines_subtotal = Decimal("0.00")
    lines_tax = Decimal("0.00")

    for line_in in data.lines:
        if plan and line_in.quantity < plan.min_quantity:
            raise AppError(
                "validation_error",
                f"Quantity {line_in.quantity} is less than plan minimum quantity {plan.min_quantity}",
                422,
                fields={"quantity": f"Must be >= {plan.min_quantity}"},
            )

        stmt = (
            select(Product)
            .options(
                selectinload(Product.attributes).selectinload(ProductAttribute.values),
                selectinload(Product.tax),
            )
            .where(Product.id == line_in.product_id)
        )
        prod = session.execute(stmt).scalar_one_or_none()
        if not prod:
            raise AppError("not_found", f"Product {line_in.product_id} not found", 404)

        snapshot = resolve_variant(prod, line_in.variant_value_ids)
        u_price = unit_price(prod, snapshot)
        l_amount = line_amount(line_in.quantity, u_price)

        # Tax
        tax_id = line_in.tax_id or prod.tax_id
        t_rate = Decimal("0.00")
        if tax_id:
            tax_obj = session.get(Tax, tax_id)
            if tax_obj:
                t_rate = to_decimal(tax_obj.rate_percent)

        l_tax = tax_amount(l_amount, t_rate)
        l_total = q2(l_amount + l_tax)

        lines_subtotal += l_amount
        lines_tax += l_tax

        out_lines.append(
            PricePreviewLine(
                product_id=prod.id,
                unit_price=u_price,
                amount=l_amount,
                tax_rate=t_rate,
                tax_amount=l_tax,
                total=l_total,
            )
        )

    grand_subtotal = q2(lines_subtotal + plan_fee_amount)
    grand_tax = q2(lines_tax + plan_fee_tax)
    grand_total = q2(grand_subtotal + grand_tax)

    return PricePreviewOut(
        lines=out_lines,
        plan_fee=plan_fee,
        totals=TotalsOut(
            subtotal=grand_subtotal,
            tax_total=grand_tax,
            total=grand_total,
        ),
    )


# ==========================================
# SUBSCRIPTION HELPERS
# ==========================================

def get_sub_or_404(session, sub_id: uuid.UUID) -> Subscription:
    stmt = (
        select(Subscription)
        .options(
            selectinload(Subscription.plan).selectinload(Plan.tax),
            selectinload(Subscription.payment_term),
            selectinload(Subscription.customer).selectinload(Customer.user),
            selectinload(Subscription.template),
            selectinload(Subscription.lines).selectinload(SubscriptionLine.product),
            selectinload(Subscription.lines).selectinload(SubscriptionLine.tax),
            selectinload(Subscription.history).selectinload(SubscriptionHistory.changed_by_user),
        )
        .where(Subscription.id == sub_id)
    )
    sub = session.execute(stmt).scalar_one_or_none()
    if not sub:
        raise AppError("not_found", f"Subscription {sub_id} not found", 404)
    return sub


def calculate_sub_totals(sub: Subscription) -> tuple[Optional[PlanFeeLine], TotalsOut, Decimal]:
    plan = sub.plan
    plan_fee = None
    plan_fee_amount = Decimal("0.00")
    plan_fee_tax = Decimal("0.00")

    if plan:
        ptax_rate = Decimal("0.00")
        if plan.tax_id:
            ptax = plan.tax
            if ptax:
                ptax_rate = to_decimal(ptax.rate_percent)
        pf_amt = to_decimal(plan.price)
        pf_tax = tax_amount(pf_amt, ptax_rate)
        plan_fee_amount = pf_amt
        plan_fee_tax = pf_tax
        plan_fee = PlanFeeLine(
            amount=pf_amt,
            tax_rate=ptax_rate,
            tax_amount=pf_tax,
            total=q2(pf_amt + pf_tax),
        )

    lines_subtotal = Decimal("0.00")
    lines_tax = Decimal("0.00")

    for line in sub.lines:
        l_amt = to_decimal(line.amount)
        l_tax = tax_amount(l_amt, to_decimal(line.tax_rate))
        lines_subtotal += l_amt
        lines_tax += l_tax

    grand_subtotal = q2(lines_subtotal + plan_fee_amount)
    grand_tax = q2(lines_tax + plan_fee_tax)
    grand_total = q2(grand_subtotal + grand_tax)

    totals = TotalsOut(
        subtotal=grand_subtotal,
        tax_total=grand_tax,
        total=grand_total,
    )
    return plan_fee, totals, grand_total


def build_subscription_detail(sub: Subscription, user: Optional[AuthUser]) -> SubscriptionDetail:
    plan_fee, totals, grand_total = calculate_sub_totals(sub)
    act_list = allowed_actions(sub, sub.plan, user)

    customer_name = sub.customer.company_name or (sub.customer.user.full_name if sub.customer.user else "Customer")
    customer_email = sub.customer.user.email if sub.customer.user else ""

    out_lines = []
    for line in sub.lines:
        l_amt = to_decimal(line.amount)
        t_rate = to_decimal(line.tax_rate)
        l_tax = tax_amount(l_amt, t_rate)
        out_lines.append(
            SubscriptionLineOut(
                id=line.id,
                product=ProductRef(id=line.product.id, name=line.product.name),
                variant=line.variant,
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax=TaxRef.model_validate(line.tax) if line.tax else None,
                tax_rate=t_rate,
                amount=l_amt,
                tax_amount=l_tax,
                total=q2(l_amt + l_tax),
            )
        )

    can_edit = (sub.status == "draft")

    return SubscriptionDetail(
        id=sub.id,
        number=sub.number,
        status=sub.status,
        customer=CustomerRef(id=sub.customer.id, name=customer_name, email=customer_email),
        plan=PlanRef(id=sub.plan.id, name=sub.plan.name, billing_period=sub.plan.billing_period),
        start_date=sub.start_date,
        expiry_date=sub.expiry_date,
        next_billing_date=sub.next_billing_date,
        estimated_total=grand_total,
        allowed_actions=act_list,
        payment_term=PaymentTermRef(
            id=sub.payment_term.id,
            name=sub.payment_term.name,
            due_days=sub.payment_term.due_days,
        ),
        quote_valid_until=sub.quote_valid_until,
        template_id=sub.quotation_template_id,
        can_edit=can_edit,
        lines=out_lines,
        plan_fee=plan_fee,
        totals=totals,
        created_at=sub.created_at,
    )


# ==========================================
# CRUD & LIFECYCLE
# ==========================================

def list_subscriptions(
    session,
    params: PageParams,
    user: AuthUser,
    *,
    status: Optional[str] = None,
    plan_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    expiring_before: Optional[datetime.date] = None,
) -> Page:
    stmt = (
        select(Subscription)
        .options(
            selectinload(Subscription.plan).selectinload(Plan.tax),
            selectinload(Subscription.customer).selectinload(Customer.user),
            selectinload(Subscription.lines),
        )
    )

    # D21: Customers see only their own rows, and never draft
    if user.role == "customer":
        if not user.customer_id:
            stmt = stmt.where(Subscription.customer_id.is_(None))
        else:
            stmt = stmt.where(Subscription.customer_id == user.customer_id)
        stmt = stmt.where(Subscription.status != "draft")
    else:
        if customer_id:
            stmt = stmt.where(Subscription.customer_id == customer_id)

    if status:
        stmt = stmt.where(Subscription.status == status)
    if plan_id:
        stmt = stmt.where(Subscription.plan_id == plan_id)
    if expiring_before:
        stmt = stmt.where(Subscription.expiry_date <= expiring_before)

    if params.q:
        search = f"%{params.q}%"
        stmt = stmt.join(Subscription.customer).outerjoin(Customer.user).where(
            or_(
                Subscription.number.ilike(search),
                Customer.company_name.ilike(search),
                User.full_name.ilike(search),
            )
        )

    allowed_sort = {
        "created_at": Subscription.created_at,
        "number": Subscription.number,
        "status": Subscription.status,
        "start_date": Subscription.start_date,
        "expiry_date": Subscription.expiry_date,
        "next_billing_date": Subscription.next_billing_date,
    }

    def map_row(sub: Subscription) -> SubscriptionListItem:
        _, _, est_total = calculate_sub_totals(sub)
        act_list = allowed_actions(sub, sub.plan, user)
        c_name = sub.customer.company_name or (sub.customer.user.full_name if sub.customer.user else "Customer")
        c_email = sub.customer.user.email if sub.customer.user else ""

        return SubscriptionListItem(
            id=sub.id,
            number=sub.number,
            status=sub.status,
            customer=CustomerRef(id=sub.customer.id, name=c_name, email=c_email),
            plan=PlanRef(id=sub.plan.id, name=sub.plan.name, billing_period=sub.plan.billing_period),
            start_date=sub.start_date,
            expiry_date=sub.expiry_date,
            next_billing_date=sub.next_billing_date,
            estimated_total=est_total,
            allowed_actions=act_list,
        )

    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort="-created_at", map_row=map_row)


def create_subscription(
    session,
    data: SubscriptionCreate,
    user: AuthUser,
) -> SubscriptionDetail:
    # 1. Validation
    if data.expiry_date <= data.start_date:
        raise AppError("validation_error", "Expiry date must be after start date", 422, fields={"expiry_date": "Must be > start_date"})

    plan = session.get(Plan, data.plan_id)
    if not plan or not plan.is_active:
        raise AppError("plan_rule_violation", "Subscription requires an active plan", 409)

    if plan.valid_from and data.start_date < plan.valid_from:
        raise AppError("plan_rule_violation", f"start_date is before plan validity start {plan.valid_from}", 409)
    if plan.valid_to and data.start_date > plan.valid_to:
        raise AppError("plan_rule_violation", f"start_date is after plan validity end {plan.valid_to}", 409)

    customer = session.get(Customer, data.customer_id)
    if not customer:
        raise AppError("not_found", f"Customer {data.customer_id} not found", 404)

    payment_term = session.get(PaymentTerm, data.payment_term_id)
    if not payment_term:
        raise AppError("not_found", f"Payment term {data.payment_term_id} not found", 404)

    # 2. Number sequence
    doc_number = next_number(session, "SUB", on=data.start_date)

    sub = Subscription(
        number=doc_number,
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        status="draft",
        start_date=data.start_date,
        expiry_date=data.expiry_date,
        payment_term_id=data.payment_term_id,
        created_by=user.id,
    )
    session.add(sub)
    session.flush()

    # 3. Lines
    for idx, line_in in enumerate(data.lines):
        if line_in.quantity < plan.min_quantity:
            raise AppError(
                "validation_error",
                f"Line {idx} quantity {line_in.quantity} < plan minimum {plan.min_quantity}",
                422,
                fields={f"lines.{idx}.quantity": f"Must be >= {plan.min_quantity}"},
            )

        stmt = (
            select(Product)
            .options(
                selectinload(Product.attributes).selectinload(ProductAttribute.values),
                selectinload(Product.tax),
            )
            .where(Product.id == line_in.product_id)
        )
        prod = session.execute(stmt).scalar_one_or_none()
        if not prod:
            raise AppError("not_found", f"Product {line_in.product_id} not found", 404)

        snapshot = resolve_variant(prod, line_in.variant_value_ids)
        u_price = unit_price(prod, snapshot)
        l_amount = line_amount(line_in.quantity, u_price)

        tax_id = line_in.tax_id or prod.tax_id
        t_rate = Decimal("0.00")
        if tax_id:
            tax_obj = session.get(Tax, tax_id)
            if tax_obj:
                t_rate = to_decimal(tax_obj.rate_percent)

        sub_line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=prod.id,
            variant=snapshot.model_dump(mode="json"),
            quantity=line_in.quantity,
            unit_price=u_price,
            tax_id=tax_id,
            tax_rate=t_rate,
            amount=l_amount,
            position=idx,
        )
        session.add(sub_line)

    # Initial history log
    history_entry = SubscriptionHistory(
        subscription_id=sub.id,
        from_status="none",
        to_status="draft",
        action="create",
        changed_by=user.id,
        changed_at=get_now(),
        note="Initial subscription draft created",
    )
    session.add(history_entry)
    session.flush()

    return build_subscription_detail(get_sub_or_404(session, sub.id), user)


def create_from_template(
    session,
    template_id: uuid.UUID,
    data: FromTemplateCreate,
    user: AuthUser,
) -> SubscriptionDetail:
    """
    D26: POST /subscriptions/from-template/{id}
    Defaults: start_date = today, expiry_date = start + 1 year,
    payment_term = first active term named 'Immediate' if omitted.
    Result is a Draft with lines copied and re-priced.
    """
    stmt = (
        select(QuotationTemplate)
        .options(
            selectinload(QuotationTemplate.plan),
            selectinload(QuotationTemplate.lines).selectinload(TemplateLine.product).selectinload(Product.attributes).selectinload(ProductAttribute.values),
            selectinload(QuotationTemplate.lines).selectinload(TemplateLine.tax),
        )
        .where(QuotationTemplate.id == template_id)
    )
    tpl = session.execute(stmt).scalar_one_or_none()
    if not tpl or not tpl.is_active:
        raise AppError("not_found", f"Active quotation template {template_id} not found", 404)

    plan = tpl.plan
    if not plan or not plan.is_active:
        raise AppError("plan_rule_violation", "Template's plan is not active", 409)

    customer = session.get(Customer, data.customer_id)
    if not customer:
        raise AppError("not_found", f"Customer {data.customer_id} not found", 404)

    start_date = data.start_date or get_today()
    expiry_date = data.expiry_date or (start_date + datetime.timedelta(days=365))

    # Payment term default
    term_id = data.payment_term_id
    if not term_id:
        imm_term = session.execute(
            select(PaymentTerm).where(func.lower(PaymentTerm.name) == "immediate", PaymentTerm.is_active == True)
        ).scalar_one_or_none()
        if imm_term:
            term_id = imm_term.id
        else:
            first_term = session.execute(
                select(PaymentTerm).where(PaymentTerm.is_active == True).order_by(PaymentTerm.due_days)
            ).scalars().first()
            if not first_term:
                raise AppError("not_found", "No active payment term found", 404)
            term_id = first_term.id

    doc_number = next_number(session, "SUB", on=start_date)
    sub = Subscription(
        number=doc_number,
        customer_id=customer.id,
        plan_id=plan.id,
        status="draft",
        start_date=start_date,
        expiry_date=expiry_date,
        payment_term_id=term_id,
        quotation_template_id=tpl.id,
        created_by=user.id,
    )
    session.add(sub)
    session.flush()

    for idx, tline in enumerate(tpl.lines):
        prod = tline.product
        val_ids = [uuid.UUID(x) for x in tline.variant.get("value_ids", [])]
        snapshot = resolve_variant(prod, val_ids)
        u_price = unit_price(prod, snapshot)
        l_amount = line_amount(tline.quantity, u_price)

        t_rate = to_decimal(tline.tax.rate_percent) if tline.tax else Decimal("0.00")
        sline = SubscriptionLine(
            subscription_id=sub.id,
            product_id=prod.id,
            variant=snapshot.model_dump(mode="json"),
            quantity=tline.quantity,
            unit_price=u_price,
            tax_id=tline.tax_id,
            tax_rate=t_rate,
            amount=l_amount,
            position=idx,
        )
        session.add(sline)

    history_entry = SubscriptionHistory(
        subscription_id=sub.id,
        from_status="none",
        to_status="draft",
        action="create_from_template",
        changed_by=user.id,
        changed_at=get_now(),
        note=f"Created from template '{tpl.name}'",
    )
    session.add(history_entry)
    session.flush()

    return build_subscription_detail(get_sub_or_404(session, sub.id), user)


def update_subscription(
    session,
    sub_id: uuid.UUID,
    data: SubscriptionUpdate,
    user: AuthUser,
) -> SubscriptionDetail:
    sub = get_sub_or_404(session, sub_id)
    assert_customer_owns(user, sub.customer_id)

    # Check editability:
    # Lines and plan only in draft
    if data.lines is not None or data.plan_id is not None:
        if sub.status != "draft":
            raise AppError("plan_rule_violation", "Lines and plan can only be modified in Draft status", 409)

    # Header fields editable in draft or quotation
    if data.start_date is not None or data.expiry_date is not None or data.payment_term_id is not None:
        if sub.status not in ("draft", "quotation"):
            raise AppError("plan_rule_violation", "Header fields can only be modified in Draft or Quotation status", 409)

    new_start = data.start_date or sub.start_date
    new_expiry = data.expiry_date or sub.expiry_date
    if new_expiry <= new_start:
        raise AppError("validation_error", "Expiry date must be after start date", 422)

    plan = sub.plan
    if data.plan_id is not None:
        new_plan = session.get(Plan, data.plan_id)
        if not new_plan or not new_plan.is_active:
            raise AppError("plan_rule_violation", "Subscription requires an active plan", 409)
        sub.plan_id = data.plan_id
        plan = new_plan

    if data.start_date is not None:
        sub.start_date = data.start_date
    if data.expiry_date is not None:
        sub.expiry_date = data.expiry_date
    if data.payment_term_id is not None:
        term = session.get(PaymentTerm, data.payment_term_id)
        if not term:
            raise AppError("not_found", f"Payment term {data.payment_term_id} not found", 404)
        sub.payment_term_id = data.payment_term_id

    if data.lines is not None:
        for old_line in list(sub.lines):
            session.delete(old_line)
        session.flush()

        for idx, line_in in enumerate(data.lines):
            if line_in.quantity < plan.min_quantity:
                raise AppError(
                    "validation_error",
                    f"Line {idx} quantity {line_in.quantity} < plan minimum {plan.min_quantity}",
                    422,
                )

            stmt = (
                select(Product)
                .options(
                    selectinload(Product.attributes).selectinload(ProductAttribute.values),
                    selectinload(Product.tax),
                )
                .where(Product.id == line_in.product_id)
            )
            prod = session.execute(stmt).scalar_one_or_none()
            if not prod:
                raise AppError("not_found", f"Product {line_in.product_id} not found", 404)

            snapshot = resolve_variant(prod, line_in.variant_value_ids)
            u_price = unit_price(prod, snapshot)
            l_amount = line_amount(line_in.quantity, u_price)

            tax_id = line_in.tax_id or prod.tax_id
            t_rate = Decimal("0.00")
            if tax_id:
                tax_obj = session.get(Tax, tax_id)
                if tax_obj:
                    t_rate = to_decimal(tax_obj.rate_percent)

            sub_line = SubscriptionLine(
                subscription_id=sub.id,
                product_id=prod.id,
                variant=snapshot.model_dump(mode="json"),
                quantity=line_in.quantity,
                unit_price=u_price,
                tax_id=tax_id,
                tax_rate=t_rate,
                amount=l_amount,
                position=idx,
            )
            session.add(sub_line)

    session.flush()
    return build_subscription_detail(get_sub_or_404(session, sub.id), user)


def delete_subscription(session, sub_id: uuid.UUID, user: AuthUser) -> dict:
    sub = get_sub_or_404(session, sub_id)
    assert_customer_owns(user, sub.customer_id)

    if sub.status != "draft":
        raise AppError("invalid_transition", "Only Draft subscriptions can be deleted", 409)

    session.delete(sub)
    session.flush()
    return {"action": "deleted", "id": str(sub_id)}


def get_history(session, sub_id: uuid.UUID, user: AuthUser) -> List[HistoryItem]:
    sub = get_sub_or_404(session, sub_id)
    assert_customer_owns(user, sub.customer_id)
    if user.role == "customer" and sub.status == "draft":
        raise AppError("not_found", "Subscription not found", 404)

    stmt = (
        select(SubscriptionHistory)
        .options(selectinload(SubscriptionHistory.changed_by_user))
        .where(SubscriptionHistory.subscription_id == sub_id)
        .order_by(SubscriptionHistory.changed_at.desc())
    )
    rows = session.execute(stmt).scalars().all()

    items = []
    for r in rows:
        c_user = None
        if r.changed_by_user:
            c_user = UserRef(id=r.changed_by_user.id, name=r.changed_by_user.full_name or r.changed_by_user.email)
        items.append(
            HistoryItem(
                id=r.id,
                from_status=r.from_status,
                to_status=r.to_status,
                action=r.action,
                changed_by=c_user,
                changed_at=r.changed_at,
                note=r.note,
            )
        )
    return items
