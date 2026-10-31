import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.deps import AuthUser, require_role, assert_customer_owns
from app.core.errors import AppError
from app.core.pagination import PageParams, page_params, Page
from app.subscriptions.schemas import (
    SubscriptionListItem,
    SubscriptionDetail,
    HistoryItem,
    TransitionInput,
)
from app.subscriptions import service
from app.subscriptions.state import transition

portal_router = APIRouter(tags=["portal"])


@portal_router.get(
    "/me/subscriptions",
    response_model=Page[SubscriptionListItem],
    summary="List customer's own subscriptions (excludes Drafts)",
)
def portal_list_subscriptions_endpoint(
    params: PageParams = Depends(page_params),
    user: AuthUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    return service.list_subscriptions(session, params, user)


@portal_router.get(
    "/me/subscriptions/{id}",
    response_model=SubscriptionDetail,
    summary="Get customer's own subscription detail (404 on Draft or other customer)",
)
def portal_get_subscription_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    sub = service.get_sub_or_404(session, id)
    assert_customer_owns(user, sub.customer_id)
    if sub.status == "draft":
        raise AppError("not_found", "Subscription not found", 404)
    return service.build_subscription_detail(sub, user)


@portal_router.post(
    "/me/subscriptions/{id}/actions",
    response_model=SubscriptionDetail,
    summary="Customer perform action on own subscription (pause, resume, close, renew)",
)
def portal_subscription_action_endpoint(
    id: uuid.UUID,
    data: TransitionInput,
    user: AuthUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    sub = service.get_sub_or_404(session, id)
    assert_customer_owns(user, sub.customer_id)
    if sub.status == "draft":
        raise AppError("not_found", "Subscription not found", 404)

    transition(session, sub, data.action, user, note=data.note)
    session.commit()
    return service.build_subscription_detail(service.get_sub_or_404(session, id), user)


@portal_router.get(
    "/me/subscriptions/{id}/history",
    response_model=List[HistoryItem],
    summary="Get history timeline for customer's own subscription",
)
def portal_subscription_history_endpoint(
    id: uuid.UUID,
    user: AuthUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    return service.get_history(session, id, user)
