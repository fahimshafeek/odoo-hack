"""Payments router."""
from fastapi import APIRouter
from app.billing.router import router as billing_router, portal_router as billing_portal_router

# All payment endpoints are included in billing router / portal router
router = APIRouter(tags=["payments"])
portal_router = APIRouter(tags=["portal_payments"])
