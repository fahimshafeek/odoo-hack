import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.deps import AuthUser, require_role
from app.core.pagination import PageParams, page_params, Page
from app.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    FromTemplateCreate,
    SubscriptionListItem,
    SubscriptionDetail,
    HistoryItem,
    TransitionInput,
    PricePreviewInput,
    PricePreviewOut,
)
from app.subscriptions import service
from app.subscriptions.state import transition

router = APIRouter(tags=["subscriptions"])


@router.post(
    "/subscriptions/price-preview",
    response_model=PricePreviewOut,
    summary="Compute live preview of prices, taxes, and totals before saving",
)
def price_preview_endpoint(
    data: PricePreviewInput,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.preview_pricing(session, data)


@router.get(
    "/subscriptions",
    response_model=Page[SubscriptionListItem],
    summary="List subscriptions with filters and allowed actions",
)
def list_subscriptions_endpoint(
    params: PageParams = Depends(page_params),
    status: Optional[str] = Query(None, description="Status filter (draft, quotation, confirmed, active, paused, closed)"),
    plan_id: Optional[uuid.UUID] = Query(None, description="Plan filter"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Customer filter"),
    expiring_before: Optional[datetime.date] = Query(None, description="Expiring on or before date"),
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.list_subscriptions(
        session,
        params,
        user,
        status=status,
        plan_id=plan_id,
        customer_id=customer_id,
        expiring_before=expiring_before,
    )


@router.post(
    "/subscriptions",
    response_model=SubscriptionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft subscription",
)
def create_subscription_endpoint(
    data: SubscriptionCreate,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    res = service.create_subscription(session, data, user)
    session.commit()
    return res


@router.post(
    "/subscriptions/from-template/{id}",
    response_model=SubscriptionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft subscription from a quotation template (D26)",
)
def create_from_template_endpoint(
    id: uuid.UUID,
    data: FromTemplateCreate,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    res = service.create_from_template(session, id, data, user)
    session.commit()
    return res


@router.get(
    "/subscriptions/{id}",
    response_model=SubscriptionDetail,
    summary="Get subscription detail with lines, totals and allowed actions",
)
def get_subscription_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    sub = service.get_sub_or_404(session, id)
    return service.build_subscription_detail(sub, user)


@router.patch(
    "/subscriptions/{id}",
    response_model=SubscriptionDetail,
    summary="Update subscription (lines/plan in Draft; headers in Draft/Quotation)",
)
def update_subscription_endpoint(
    id: uuid.UUID,
    data: SubscriptionUpdate,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    res = service.update_subscription(session, id, data, user)
    session.commit()
    return res


@router.delete(
    "/subscriptions/{id}",
    summary="Delete subscription (Draft only)",
)
def delete_subscription_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    res = service.delete_subscription(session, id, user)
    session.commit()
    return res


@router.post(
    "/subscriptions/{id}/transition",
    response_model=SubscriptionDetail,
    summary="Execute state machine transition on subscription",
)
def transition_subscription_endpoint(
    id: uuid.UUID,
    data: TransitionInput,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    sub = service.get_sub_or_404(session, id)
    transition(session, sub, data.action, user, note=data.note)
    session.commit()
    return service.build_subscription_detail(service.get_sub_or_404(session, id), user)


@router.get(
    "/subscriptions/{id}/history",
    response_model=List[HistoryItem],
    summary="Get subscription status history timeline",
)
def get_subscription_history_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session),
):
    return service.get_history(session, id, user)
