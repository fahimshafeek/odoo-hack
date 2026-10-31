from fastapi import APIRouter

router = APIRouter(tags=["subscriptions"])
portal_router = APIRouter(tags=["portal_subscriptions"])

@router.get("/subscriptions")
def list_subscriptions():
    return {"items": [], "total": 0, "message": "Subscriptions router placeholder for M2"}
