import uuid
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.core.errors import AppError
from app.core.pagination import PageParams, Page, paginate
from app.core.money import to_decimal, q2, tax_amount
from app.catalog.models import (
    Tax,
    Product,
    ProductAttribute,
    AttributeValue,
    Plan,
    PaymentTerm,
    QuotationTemplate,
    TemplateLine,
)
from app.catalog.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductDetail,
    ProductListItem,
    ProductAttributeCreate,
    ProductAttributeUpdate,
    PlanCreate,
    PlanUpdate,
    PlanListItem,
    PaymentTermCreate,
    PaymentTermUpdate,
    QuotationTemplateCreate,
    QuotationTemplateUpdate,
    QuotationTemplateDetail,
    QuotationTemplateListItem,
    TemplateLineOut,
    ProductRef,
    PlanRef,
    TaxRef,
)
from app.subscriptions.pricing import resolve_variant, unit_price, line_amount


# ==========================================
# PRODUCTS
# ==========================================

def get_product_or_404(session, product_id: uuid.UUID) -> Product:
    stmt = (
        select(Product)
        .options(
            selectinload(Product.tax),
            selectinload(Product.attributes).selectinload(ProductAttribute.values),
        )
        .where(Product.id == product_id)
    )
    product = session.execute(stmt).scalar_one_or_none()
    if not product:
        raise AppError("not_found", f"Product {product_id} not found", 404)
    return product


def build_product_detail(product: Product) -> ProductDetail:
    warnings = []
    if to_decimal(product.cost_price) > to_decimal(product.sales_price):
        warnings.append("cost_price_exceeds_sales_price")

    tax_ref = None
    if product.tax_id and "tax" in product.__dict__ and product.__dict__["tax"] is not None:
        tax_ref = TaxRef.model_validate(product.tax)

    attrs = []
    if "attributes" in product.__dict__ and product.__dict__["attributes"] is not None:
        attrs = product.attributes

    return ProductDetail(
        id=product.id,
        name=product.name,
        type=product.type,
        sales_price=product.sales_price,
        cost_price=product.cost_price,
        notes=product.notes,
        tax_id=product.tax_id,
        tax=tax_ref,
        is_active=product.is_active,
        attributes=attrs,
        warnings=warnings,
    )


def build_product_list_item(product: Product) -> ProductListItem:
    tax_ref = None
    if product.tax_id and "tax" in product.__dict__ and product.__dict__["tax"] is not None:
        tax_ref = TaxRef.model_validate(product.tax)

    return ProductListItem(
        id=product.id,
        name=product.name,
        type=product.type,
        sales_price=product.sales_price,
        cost_price=product.cost_price,
        tax=tax_ref,
        is_active=product.is_active,
    )


def build_plan_item(plan: Plan) -> PlanListItem:
    tax_ref = None
    if plan.tax_id and "tax" in plan.__dict__ and plan.__dict__["tax"] is not None:
        tax_ref = TaxRef.model_validate(plan.tax)

    return PlanListItem(
        id=plan.id,
        name=plan.name,
        price=plan.price,
        billing_period=plan.billing_period,
        min_quantity=plan.min_quantity,
        valid_from=plan.valid_from,
        valid_to=plan.valid_to,
        tax=tax_ref,
        tax_id=plan.tax_id,
        auto_close=plan.auto_close,
        allow_early_close=plan.allow_early_close,
        allow_pause=plan.allow_pause,
        allow_renew=plan.allow_renew,
        is_active=plan.is_active,
    )


def list_products(
    session,
    params: PageParams,
    *,
    type: Optional[str] = None,
    active: Optional[bool] = None,
) -> Page:
    stmt = select(Product).options(selectinload(Product.tax))
    if type:
        stmt = stmt.where(Product.type == type)
    if active is not None:
        stmt = stmt.where(Product.is_active == active)
    if params.q:
        search = f"%{params.q}%"
        stmt = stmt.where(or_(Product.name.ilike(search), Product.type.ilike(search)))

    allowed_sort = {
        "created_at": Product.created_at,
        "name": Product.name,
        "sales_price": Product.sales_price,
        "cost_price": Product.cost_price,
    }

    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort="-created_at", map_row=build_product_list_item)


def create_product(session, data: ProductCreate) -> ProductDetail:
    if data.tax_id:
        tax = session.get(Tax, data.tax_id)
        if not tax:
            raise AppError("validation_error", "Tax does not exist", 422, fields={"tax_id": "Invalid tax ID"})

    product = Product(
        name=data.name,
        type=data.type,
        sales_price=data.sales_price,
        cost_price=data.cost_price,
        notes=data.notes,
        tax_id=data.tax_id,
        is_active=data.is_active,
    )
    session.add(product)
    session.flush()
    session.expire(product)
    return build_product_detail(get_product_or_404(session, product.id))


def update_product(session, product_id: uuid.UUID, data: ProductUpdate) -> ProductDetail:
    product = get_product_or_404(session, product_id)

    if data.tax_id is not None:
        tax = session.get(Tax, data.tax_id)
        if not tax:
            raise AppError("validation_error", "Tax does not exist", 422, fields={"tax_id": "Invalid tax ID"})
        product.tax_id = data.tax_id

    if data.name is not None:
        product.name = data.name
    if data.type is not None:
        product.type = data.type
    if data.sales_price is not None:
        product.sales_price = data.sales_price
    if data.cost_price is not None:
        product.cost_price = data.cost_price
    if data.notes is not None:
        product.notes = data.notes
    if data.is_active is not None:
        product.is_active = data.is_active

    session.flush()
    return build_product_detail(product)


def delete_product(session, product_id: uuid.UUID) -> dict:
    product = get_product_or_404(session, product_id)
    # Check references in subscription_lines or template_lines
    from app.subscriptions.models import SubscriptionLine
    has_sub = session.execute(
        select(func.count(SubscriptionLine.id)).where(SubscriptionLine.product_id == product_id)
    ).scalar() or 0
    has_tpl = session.execute(
        select(func.count(TemplateLine.id)).where(TemplateLine.product_id == product_id)
    ).scalar() or 0

    if has_sub > 0 or has_tpl > 0:
        product.is_active = False
        session.flush()
        return {"action": "deactivated", "id": str(product_id)}

    session.delete(product)
    session.flush()
    return {"action": "deleted", "id": str(product_id)}


# --- Attributes & Values ---

def add_product_attribute(session, product_id: uuid.UUID, data: ProductAttributeCreate) -> ProductDetail:
    product = get_product_or_404(session, product_id)

    # Check attribute name uniqueness for this product
    for attr in product.attributes:
        if attr.name.lower() == data.name.strip().lower():
            raise AppError("conflict", f"Attribute '{data.name}' already exists on this product", 409)

    # Check value names uniqueness
    seen_vals = set()
    for val in data.values:
        v_norm = val.name.strip().lower()
        if v_norm in seen_vals:
            raise AppError("validation_error", f"Duplicate attribute value name '{val.name}'", 422)
        seen_vals.add(v_norm)

    new_attr = ProductAttribute(
        product_id=product.id,
        name=data.name.strip(),
    )
    session.add(new_attr)
    session.flush()

    for val in data.values:
        new_val = AttributeValue(
            attribute_id=new_attr.id,
            name=val.name.strip(),
            extra_price=val.extra_price,
        )
        session.add(new_val)

    session.flush()
    session.expire(product)
    return build_product_detail(get_product_or_404(session, product.id))


def update_product_attribute(
    session,
    product_id: uuid.UUID,
    attr_id: uuid.UUID,
    data: ProductAttributeUpdate,
) -> ProductDetail:
    product = get_product_or_404(session, product_id)
    attr = session.get(ProductAttribute, attr_id)
    if not attr or attr.product_id != product_id:
        raise AppError("not_found", f"Attribute {attr_id} not found on product", 404)

    # Check attribute name uniqueness against other attributes
    for other in product.attributes:
        if other.id != attr_id and other.name.lower() == data.name.strip().lower():
            raise AppError("conflict", f"Attribute '{data.name}' already exists on this product", 409)

    attr.name = data.name.strip()

    # Values diff: items with id updated, without id created, omitted deleted
    input_ids = {v.id for v in data.values if v.id is not None}
    current_values = {v.id: v for v in attr.values}

    # Delete omitted
    for cur_id, cur_val in list(current_values.items()):
        if cur_id not in input_ids:
            session.delete(cur_val)

    # Create or update
    for val_input in data.values:
        if val_input.id and val_input.id in current_values:
            target = current_values[val_input.id]
            target.name = val_input.name.strip()
            target.extra_price = val_input.extra_price
        else:
            new_v = AttributeValue(
                attribute_id=attr.id,
                name=val_input.name.strip(),
                extra_price=val_input.extra_price,
            )
            session.add(new_v)

    session.flush()
    session.expire(product)
    return build_product_detail(get_product_or_404(session, product.id))


def delete_product_attribute(session, product_id: uuid.UUID, attr_id: uuid.UUID) -> ProductDetail:
    product = get_product_or_404(session, product_id)
    attr = session.get(ProductAttribute, attr_id)
    if not attr or attr.product_id != product_id:
        raise AppError("not_found", f"Attribute {attr_id} not found on product", 404)

    session.delete(attr)
    session.flush()
    session.expire(product)
    return build_product_detail(get_product_or_404(session, product.id))


# ==========================================
# PLANS
# ==========================================

def get_plan_or_404(session, plan_id: uuid.UUID) -> Plan:
    stmt = (
        select(Plan)
        .options(selectinload(Plan.tax))
        .where(Plan.id == plan_id)
    )
    plan = session.execute(stmt).scalar_one_or_none()
    if not plan:
        raise AppError("not_found", f"Plan {plan_id} not found", 404)
    return plan


def list_plans(session, params: PageParams, *, active: Optional[bool] = None) -> Page:
    stmt = select(Plan).options(selectinload(Plan.tax))
    if active is not None:
        stmt = stmt.where(Plan.is_active == active)
    if params.q:
        stmt = stmt.where(Plan.name.ilike(f"%{params.q}%"))

    allowed_sort = {
        "created_at": Plan.created_at,
        "name": Plan.name,
        "price": Plan.price,
    }
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort="-created_at", map_row=build_plan_item)


def create_plan(session, data: PlanCreate) -> Plan:
    if data.valid_from and data.valid_to and data.valid_to < data.valid_from:
        raise AppError("validation_error", "valid_to cannot be earlier than valid_from", 422, fields={"valid_to": "Must be >= valid_from"})

    if data.tax_id:
        tax = session.get(Tax, data.tax_id)
        if not tax:
            raise AppError("validation_error", "Tax does not exist", 422, fields={"tax_id": "Invalid tax ID"})

    plan = Plan(
        name=data.name.strip(),
        price=data.price,
        billing_period=data.billing_period,
        min_quantity=data.min_quantity,
        valid_from=data.valid_from,
        valid_to=data.valid_to,
        tax_id=data.tax_id,
        auto_close=data.auto_close,
        allow_early_close=data.allow_early_close,
        allow_pause=data.allow_pause,
        allow_renew=data.allow_renew,
        is_active=data.is_active,
    )
    session.add(plan)
    session.flush()
    return build_plan_item(get_plan_or_404(session, plan.id))


def update_plan(session, plan_id: uuid.UUID, data: PlanUpdate) -> PlanListItem:
    plan = get_plan_or_404(session, plan_id)

    new_from = data.valid_from if data.valid_from is not None else plan.valid_from
    new_to = data.valid_to if data.valid_to is not None else plan.valid_to
    if new_from and new_to and new_to < new_from:
        raise AppError("validation_error", "valid_to cannot be earlier than valid_from", 422, fields={"valid_to": "Must be >= valid_from"})

    if data.tax_id is not None:
        tax = session.get(Tax, data.tax_id)
        if not tax:
            raise AppError("validation_error", "Tax does not exist", 422, fields={"tax_id": "Invalid tax ID"})
        plan.tax_id = data.tax_id

    for field, val in data.model_dump(exclude_unset=True).items():
        if field != "tax_id":
            setattr(plan, field, val)

    session.flush()
    return build_plan_item(get_plan_or_404(session, plan.id))


def close_plan(session, plan_id: uuid.UUID) -> PlanListItem:
    """Sets is_active=false. Existing subscriptions keep running, plan can't be sold."""
    plan = get_plan_or_404(session, plan_id)
    plan.is_active = False
    session.flush()
    return build_plan_item(plan)


def delete_plan(session, plan_id: uuid.UUID) -> dict:
    plan = get_plan_or_404(session, plan_id)
    from app.subscriptions.models import Subscription
    has_sub = session.execute(
        select(func.count(Subscription.id)).where(Subscription.plan_id == plan_id)
    ).scalar() or 0
    has_tpl = session.execute(
        select(func.count(QuotationTemplate.id)).where(QuotationTemplate.plan_id == plan_id)
    ).scalar() or 0

    if has_sub > 0 or has_tpl > 0:
        plan.is_active = False
        session.flush()
        return {"action": "deactivated", "id": str(plan_id)}

    session.delete(plan)
    session.flush()
    return {"action": "deleted", "id": str(plan_id)}


# ==========================================
# PAYMENT TERMS
# ==========================================

def get_payment_term_or_404(session, term_id: uuid.UUID) -> PaymentTerm:
    term = session.get(PaymentTerm, term_id)
    if not term:
        raise AppError("not_found", f"Payment term {term_id} not found", 404)
    return term


def list_payment_terms(session, params: PageParams, *, active: Optional[bool] = None) -> Page:
    stmt = select(PaymentTerm)
    if active is not None:
        stmt = stmt.where(PaymentTerm.is_active == active)
    if params.q:
        stmt = stmt.where(PaymentTerm.name.ilike(f"%{params.q}%"))

    allowed_sort = {
        "created_at": PaymentTerm.created_at,
        "name": PaymentTerm.name,
        "due_days": PaymentTerm.due_days,
    }
    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort="due_days")


def create_payment_term(session, data: PaymentTermCreate) -> PaymentTerm:
    existing = session.execute(
        select(PaymentTerm).where(func.lower(PaymentTerm.name) == data.name.strip().lower())
    ).scalar_one_or_none()
    if existing:
        raise AppError("conflict", f"Payment term '{data.name}' already exists", 409)

    term = PaymentTerm(
        name=data.name.strip(),
        due_days=data.due_days,
    )
    session.add(term)
    session.flush()
    return term


def update_payment_term(session, term_id: uuid.UUID, data: PaymentTermUpdate) -> PaymentTerm:
    term = get_payment_term_or_404(session, term_id)
    if data.name is not None:
        existing = session.execute(
            select(PaymentTerm).where(
                func.lower(PaymentTerm.name) == data.name.strip().lower(),
                PaymentTerm.id != term_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise AppError("conflict", f"Payment term '{data.name}' already exists", 409)
        term.name = data.name.strip()

    if data.due_days is not None:
        term.due_days = data.due_days
    if data.is_active is not None:
        term.is_active = data.is_active

    session.flush()
    return term


def delete_payment_term(session, term_id: uuid.UUID) -> dict:
    term = get_payment_term_or_404(session, term_id)
    from app.subscriptions.models import Subscription
    has_sub = session.execute(
        select(func.count(Subscription.id)).where(Subscription.payment_term_id == term_id)
    ).scalar() or 0
    if has_sub > 0:
        term.is_active = False
        session.flush()
        return {"action": "deactivated", "id": str(term_id)}

    session.delete(term)
    session.flush()
    return {"action": "deleted", "id": str(term_id)}


# ==========================================
# QUOTATION TEMPLATES
# ==========================================

def get_template_or_404(session, template_id: uuid.UUID) -> QuotationTemplate:
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
    if not tpl:
        raise AppError("not_found", f"Quotation template {template_id} not found", 404)
    return tpl


def build_template_detail(tpl: QuotationTemplate) -> QuotationTemplateDetail:
    out_lines = []
    for line in tpl.lines:
        prod = line.product
        val_ids = [uuid.UUID(x) for x in line.variant.get("value_ids", [])]
        snapshot = resolve_variant(prod, val_ids)
        u_price = unit_price(prod, snapshot)
        l_amount = line_amount(line.quantity, u_price)
        t_rate = to_decimal(line.tax.rate_percent) if line.tax else to_decimal("0.00")

        out_lines.append(
            TemplateLineOut(
                id=line.id,
                product=ProductRef(id=prod.id, name=prod.name),
                variant=snapshot.model_dump(mode="json"),
                quantity=line.quantity,
                unit_price=u_price,
                tax=TaxRef.model_validate(line.tax) if line.tax else None,
                tax_rate=t_rate,
                amount=l_amount,
                position=line.position,
            )
        )

    return QuotationTemplateDetail(
        id=tpl.id,
        name=tpl.name,
        plan=PlanRef(id=tpl.plan.id, name=tpl.plan.name, billing_period=tpl.plan.billing_period),
        plan_id=tpl.plan_id,
        validity_days=tpl.validity_days,
        is_active=tpl.is_active,
        lines=out_lines,
    )


def list_templates(session, params: PageParams, *, active: Optional[bool] = None) -> Page:
    stmt = select(QuotationTemplate).options(selectinload(QuotationTemplate.plan), selectinload(QuotationTemplate.lines))
    if active is not None:
        stmt = stmt.where(QuotationTemplate.is_active == active)
    if params.q:
        stmt = stmt.where(QuotationTemplate.name.ilike(f"%{params.q}%"))

    allowed_sort = {
        "created_at": QuotationTemplate.created_at,
        "name": QuotationTemplate.name,
        "validity_days": QuotationTemplate.validity_days,
    }

    def map_row(tpl: QuotationTemplate) -> QuotationTemplateListItem:
        return QuotationTemplateListItem(
            id=tpl.id,
            name=tpl.name,
            plan=PlanRef(id=tpl.plan.id, name=tpl.plan.name, billing_period=tpl.plan.billing_period),
            validity_days=tpl.validity_days,
            is_active=tpl.is_active,
            lines_count=len(tpl.lines),
        )

    return paginate(session, stmt, params, allowed_sort=allowed_sort, default_sort="-created_at", map_row=map_row)


def create_template(session, data: QuotationTemplateCreate) -> QuotationTemplateDetail:
    plan = session.get(Plan, data.plan_id)
    if not plan or not plan.is_active:
        raise AppError("plan_rule_violation", "Quotation template requires an active plan", 409)

    tpl = QuotationTemplate(
        name=data.name.strip(),
        plan_id=data.plan_id,
        validity_days=data.validity_days,
    )
    session.add(tpl)
    session.flush()

    for idx, line_in in enumerate(data.lines):
        prod = get_product_or_404(session, line_in.product_id)
        # Validate variant
        snapshot = resolve_variant(prod, line_in.variant_value_ids)
        tax_id = line_in.tax_id or prod.tax_id

        tpl_line = TemplateLine(
            template_id=tpl.id,
            product_id=prod.id,
            variant={"value_ids": [str(vid) for vid in line_in.variant_value_ids]},
            quantity=line_in.quantity,
            position=idx,
            tax_id=tax_id,
        )
        session.add(tpl_line)

    session.flush()
    return build_template_detail(get_template_or_404(session, tpl.id))


def update_template(session, template_id: uuid.UUID, data: QuotationTemplateUpdate) -> QuotationTemplateDetail:
    tpl = get_template_or_404(session, template_id)
    if data.plan_id is not None:
        plan = session.get(Plan, data.plan_id)
        if not plan or not plan.is_active:
            raise AppError("plan_rule_violation", "Quotation template requires an active plan", 409)
        tpl.plan_id = data.plan_id

    if data.name is not None:
        tpl.name = data.name.strip()
    if data.validity_days is not None:
        tpl.validity_days = data.validity_days
    if data.is_active is not None:
        tpl.is_active = data.is_active

    if data.lines is not None:
        for old_line in list(tpl.lines):
            session.delete(old_line)
        session.flush()

        for idx, line_in in enumerate(data.lines):
            prod = get_product_or_404(session, line_in.product_id)
            resolve_variant(prod, line_in.variant_value_ids)
            tax_id = line_in.tax_id or prod.tax_id
            tpl_line = TemplateLine(
                template_id=tpl.id,
                product_id=prod.id,
                variant={"value_ids": [str(vid) for vid in line_in.variant_value_ids]},
                quantity=line_in.quantity,
                position=idx,
                tax_id=tax_id,
            )
            session.add(tpl_line)

    session.flush()
    return build_template_detail(get_template_or_404(session, tpl.id))


def delete_template(session, template_id: uuid.UUID) -> dict:
    tpl = get_template_or_404(session, template_id)
    from app.subscriptions.models import Subscription
    has_sub = session.execute(
        select(func.count(Subscription.id)).where(Subscription.quotation_template_id == template_id)
    ).scalar() or 0
    if has_sub > 0:
        tpl.is_active = False
        session.flush()
        return {"action": "deactivated", "id": str(template_id)}

    session.delete(tpl)
    session.flush()
    return {"action": "deleted", "id": str(template_id)}
