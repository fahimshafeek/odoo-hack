from typing import Any, Optional


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        status: Optional[int] = None,
        details: Any = None,
        fields: Any = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status if status is not None else status_code
        self.status = self.status_code
        self.fields = fields or (details.get("fields") if isinstance(details, dict) and "fields" in details else {})
        self.details = details if details is not None else ({"fields": self.fields} if self.fields else None)
        super().__init__(message)
