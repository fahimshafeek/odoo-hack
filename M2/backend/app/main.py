import logging
import uuid
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from app.core.database import Base, engine, SessionLocal
from app.core.errors import AppError
from app.core.security import create_access_token
from app.core.models import User, Customer
from app.catalog.router import router as catalog_router
from app.subscriptions.router import router as subscriptions_router
from app.subscriptions.portal_router import portal_router as subscriptions_portal_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("brightloop.main")

# Auto-create tables on import/startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Brightloop Subscription Management System - M2 Catalog & Subscriptions",
    version="1.0.0",
    description="API for Products, Variants, Plans, Quotation Templates, and Subscriptions lifecycle.",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = {}
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"] if part not in ("body",))
        fields[loc or "body"] = err["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Input validation failed",
                "fields": fields,
            }
        },
    )


# Include Routers
app.include_router(catalog_router)
app.include_router(subscriptions_router)
app.include_router(subscriptions_portal_router)


# Quick Dev/Demo Auth Endpoint
class LoginRequest(BaseModel):
    role: str = "admin"  # admin | staff | customer
    email: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None


@app.post("/auth/demo-token", tags=["auth"], summary="Generate a quick demo JWT token for testing")
def generate_demo_token(data: LoginRequest):
    """Convenience endpoint for frontend and testing to get tokens for different roles."""
    user_id = uuid.uuid4()
    email = data.email or f"{data.role}@brightloop.local"
    full_name = f"Demo {data.role.capitalize()}"

    # If customer role and no customer_id, find or create one in db
    cid = data.customer_id
    if data.role == "customer" and not cid:
        db = SessionLocal()
        try:
            cust = db.query(Customer).first()
            if cust:
                cid = cust.id
        finally:
            db.close()

    token = create_access_token(
        user_id=user_id,
        role=data.role,
        customer_id=cid,
        full_name=full_name,
        email=email,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user_id),
            "email": email,
            "role": data.role,
            "customer_id": str(cid) if cid else None,
            "full_name": full_name,
        },
    }


@app.get("/health", tags=["system"], summary="Health check")
def health_check():
    return {"status": "ok", "module": "M2_catalog_subscriptions", "database": "sqlite"}
