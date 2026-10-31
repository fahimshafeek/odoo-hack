from fastapi import APIRouter

router = APIRouter(tags=["payments"])
portal_router = APIRouter(tags=["portal_payments"])

@router.get("/payments")
def list_payments():
    return {"items": [], "total": 0, "message": "Payments router placeholder for M3"}
