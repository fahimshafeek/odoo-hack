import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.deps import AuthUser, require_role
from app.core.pagination import PageParams, page_params, Page
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
    PaymentTermOut,
    QuotationTemplateCreate,
    QuotationTemplateUpdate,
    QuotationTemplateDetail,
    QuotationTemplateListItem,
)
from app.catalog import service

router = APIRouter(tags=["catalog"])
portal_router = APIRouter(tags=["catalog_portal"])  # Empty portal router for catalog


# ==========================================
# PRODUCTS
# ==========================================

@router.get(
    "/products",
    response_model=Page[ProductListItem],
    summary="List products with pagination and filters",
)
def list_products_endpoint(
    params: PageParams = Depends(page_params),
    type: Optional[str] = Query(None, description="Product type filter"),
    active: Optional[bool] = Query(None, description="Active status filter"),
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.list_products(session, params, type=type, active=active)


@router.post(
    "/products",
    response_model=ProductDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)",
)
def create_product_endpoint(
    data: ProductCreate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.create_product(session, data)
    session.commit()
    return res


@router.get(
    "/products/{id}",
    response_model=ProductDetail,
    summary="Get product detail with attributes and variant values",
)
def get_product_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    prod = service.get_product_or_404(session, id)
    return service.build_product_detail(prod)


@router.patch(
    "/products/{id}",
    response_model=ProductDetail,
    summary="Update product details (Admin only)",
)
def update_product_endpoint(
    id: uuid.UUID,
    data: ProductUpdate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.update_product(session, id, data)
    session.commit()
    return res


@router.delete(
    "/products/{id}",
    summary="Delete or deactivate product (Admin only)",
)
def delete_product_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.delete_product(session, id)
    session.commit()
    return res


@router.post(
    "/products/{id}/attributes",
    response_model=ProductDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Add attribute and values to product (Admin only)",
)
def add_product_attribute_endpoint(
    id: uuid.UUID,
    data: ProductAttributeCreate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.add_product_attribute(session, id, data)
    session.commit()
    return res


@router.patch(
    "/products/{id}/attributes/{attr_id}",
    response_model=ProductDetail,
    summary="Update attribute and values on product (Admin only)",
)
def update_product_attribute_endpoint(
    id: uuid.UUID,
    attr_id: uuid.UUID,
    data: ProductAttributeUpdate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.update_product_attribute(session, id, attr_id, data)
    session.commit()
    return res


@router.delete(
    "/products/{id}/attributes/{attr_id}",
    response_model=ProductDetail,
    summary="Delete attribute from product (Admin only)",
)
def delete_product_attribute_endpoint(
    id: uuid.UUID,
    attr_id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.delete_product_attribute(session, id, attr_id)
    session.commit()
    return res


# ==========================================
# PLANS
# ==========================================

@router.get(
    "/plans",
    response_model=Page[PlanListItem],
    summary="List plans with pagination and active filter",
)
def list_plans_endpoint(
    params: PageParams = Depends(page_params),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.list_plans(session, params, active=active)


@router.post(
    "/plans",
    response_model=PlanListItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new plan with rules (Admin only)",
)
def create_plan_endpoint(
    data: PlanCreate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.create_plan(session, data)
    session.commit()
    return res


@router.get(
    "/plans/{id}",
    response_model=PlanListItem,
    summary="Get plan detail",
)
def get_plan_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    plan = service.get_plan_or_404(session, id)
    return service.build_plan_item(plan)


@router.patch(
    "/plans/{id}",
    response_model=PlanListItem,
    summary="Update plan details and rules (Admin only)",
)
def update_plan_endpoint(
    id: uuid.UUID,
    data: PlanUpdate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.update_plan(session, id, data)
    session.commit()
    return res


@router.post(
    "/plans/{id}/close",
    response_model=PlanListItem,
    summary="Close plan (sets is_active=false, prevents new sales, Admin only)",
)
def close_plan_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.close_plan(session, id)
    session.commit()
    return res


@router.delete(
    "/plans/{id}",
    summary="Delete or deactivate plan (Admin only)",
)
def delete_plan_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.delete_plan(session, id)
    session.commit()
    return res


# ==========================================
# PAYMENT TERMS
# ==========================================

@router.get(
    "/payment-terms",
    response_model=Page[PaymentTermOut],
    summary="List payment terms",
)
def list_payment_terms_endpoint(
    params: PageParams = Depends(page_params),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.list_payment_terms(session, params, active=active)


@router.post(
    "/payment-terms",
    response_model=PaymentTermOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment term (Admin only)",
)
def create_payment_term_endpoint(
    data: PaymentTermCreate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.create_payment_term(session, data)
    session.commit()
    return res


@router.get(
    "/payment-terms/{id}",
    response_model=PaymentTermOut,
    summary="Get payment term detail",
)
def get_payment_term_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.get_payment_term_or_404(session, id)


@router.patch(
    "/payment-terms/{id}",
    response_model=PaymentTermOut,
    summary="Update payment term (Admin only)",
)
def update_payment_term_endpoint(
    id: uuid.UUID,
    data: PaymentTermUpdate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.update_payment_term(session, id, data)
    session.commit()
    return res


@router.delete(
    "/payment-terms/{id}",
    summary="Delete or deactivate payment term (Admin only)",
)
def delete_payment_term_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.delete_payment_term(session, id)
    session.commit()
    return res


# ==========================================
# QUOTATION TEMPLATES
# ==========================================

@router.get(
    "/quotation-templates",
    response_model=Page[QuotationTemplateListItem],
    summary="List quotation templates",
)
def list_quotation_templates_endpoint(
    params: PageParams = Depends(page_params),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.list_templates(session, params, active=active)


@router.post(
    "/quotation-templates",
    response_model=QuotationTemplateDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create quotation template with lines (Admin only)",
)
def create_quotation_template_endpoint(
    data: QuotationTemplateCreate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.create_template(session, data)
    session.commit()
    return res


@router.get(
    "/quotation-templates/{id}",
    response_model=QuotationTemplateDetail,
    summary="Get quotation template detail",
)
def get_quotation_template_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    tpl = service.get_template_or_404(session, id)
    return service.build_template_detail(tpl)


@router.patch(
    "/quotation-templates/{id}",
    response_model=QuotationTemplateDetail,
    summary="Update quotation template (Admin only)",
)
def update_quotation_template_endpoint(
    id: uuid.UUID,
    data: QuotationTemplateUpdate,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.update_template(session, id, data)
    session.commit()
    return res


@router.delete(
    "/quotation-templates/{id}",
    summary="Delete or deactivate quotation template (Admin only)",
)
def delete_quotation_template_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    res = service.delete_template(session, id)
    session.commit()
    return res
