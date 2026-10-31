from fastapi import APIRouter

router = APIRouter(tags=["catalog"])
portal_router = APIRouter(tags=["portal_catalog"])

@router.get("/products")
def list_products():
    return {"items": [], "total": 0, "message": "Catalog router placeholder for M2"}

@router.get("/plans")
def list_plans():
    return {"items": [], "total": 0, "message": "Plans router placeholder for M2"}
