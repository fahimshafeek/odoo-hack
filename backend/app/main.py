from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.db import Base, engine, init_db
from app.core.errors import AppError

# Import all models to ensure registration in Base.metadata
import app.auth.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.subscriptions.models  # noqa: F401
import app.billing.models  # noqa: F401
import app.payments.models  # noqa: F401
import app.core.numbering  # noqa: F401

# Import routers
from app.auth.router import router as auth_router, portal_router as auth_portal_router
from app.catalog.router import router as catalog_router
from app.subscriptions.router import router as subscriptions_router
from app.subscriptions.portal_router import portal_router as subscriptions_portal_router
from app.billing.router import router as billing_router, portal_router as billing_portal_router
from app.reports.router import router as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist on startup
    init_db()
    yield


app = FastAPI(
    title="Brightloop API",
    description="Unified API for Brightloop Subscriptions, Billing, Payments, and Catalog.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "fields": exc.fields or {},
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = str(loc[-1]) if loc else "general"
        fields[field_name] = err.get("msg", "Invalid value")

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Validation failed for request data",
                "fields": fields,
            }
        },
    )


# Mount All Routers
app.include_router(auth_router)
app.include_router(auth_portal_router)
app.include_router(catalog_router)
app.include_router(subscriptions_router)
app.include_router(subscriptions_portal_router)
app.include_router(billing_router)
app.include_router(billing_portal_router)
app.include_router(reports_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "app": "brightloop"}
