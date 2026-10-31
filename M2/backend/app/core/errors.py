from typing import Optional, Dict


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        fields: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields or {}

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "fields": self.fields,
            }
        }
