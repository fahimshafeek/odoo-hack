from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import portal_router as auth_portal_router, router as auth_router
from app.billing.router import portal_router as billing_portal_router, router as billing_router
from app.catalog.router import portal_router as catalog_portal_router, router as catalog_router
from app.core.config import settings
from app.core.db import Base, engine
from app.core.errors import (
    AppError,
    app_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.payments.router import portal_router as payments_portal_router, router as payments_router
from app.reports.router import portal_router as reports_portal_router, router as reports_router
from app.subscriptions.router import portal_router as subscriptions_portal_router, router as subscriptions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create all tables on startup for SQLite
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Brightloop Subscription Management API",
    description="Backend API for Products, Plans, Subscriptions, Invoicing, Payments and Reporting.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Healthcheck
@app.get("/health", tags=["system"])
def healthcheck():
    return {
        "status": "healthy",
        "env": settings.ENV,
        "database": "sqlite_connected",
        "resend_email": "active" if bool(settings.RESEND_API_KEY) else "mock_mode",
    }

# Wire all routers in dependency order
app.include_router(auth_router)
app.include_router(auth_portal_router)
app.include_router(catalog_router)
app.include_router(catalog_portal_router)
app.include_router(subscriptions_router)
app.include_router(subscriptions_portal_router)
app.include_router(billing_router)
app.include_router(billing_portal_router)
app.include_router(payments_router)
app.include_router(payments_portal_router)
app.include_router(reports_router)
app.include_router(reports_portal_router)
