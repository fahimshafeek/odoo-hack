"""
FastAPI application entry point for M3: Billing & Payments.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core_compat import AppError
from app.database import init_db
from app.router import portal_router, router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Brightloop M3: Billing & Payments API",
    version="1.0.0",
    description="Billing engine, taxes, discounts, invoices, and payments management system",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content=exc.to_dict())


app.include_router(router)
app.include_router(portal_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "module": "M3: Billing & Payments"}
