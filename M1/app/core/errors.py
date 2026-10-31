from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        fields: dict[str, str] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields or {}
        super().__init__(message)

def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "fields": exc.fields,
            }
        },
    )

def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = ".".join(str(part) for part in loc if part not in ("body", "query", "path"))
        fields[field_name] = err.get("msg", "Invalid value")

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

def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred",
                "fields": {},
            }
        },
    )
