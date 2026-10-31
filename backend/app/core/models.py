"""Re-export User and Customer models for M2 compatibility."""
from app.auth.models import User, Customer

__all__ = ["User", "Customer"]
