from fastapi import APIRouter

router = APIRouter(tags=["billing"])
portal_router = APIRouter(tags=["portal_billing"])

@router.get("/invoices")
def list_invoices():
    return {"items": [], "total": 0, "message": "Billing router placeholder for M3"}
