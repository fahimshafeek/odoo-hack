from typing import Any, Generic, TypeVar
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from app.core.errors import AppError

T = TypeVar("T")

class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(25, ge=1, le=100, description="Items per page (max 100)"),
        sort: str | None = Query(None, description="Comma-separated sort keys (prefix - for desc)"),
        q: str | None = Query(None, description="Fuzzy search keyword"),
    ):
        self.page = page if isinstance(page, int) else 1
        self.page_size = page_size if isinstance(page_size, int) else 25
        self.sort = sort if isinstance(sort, str) else None
        self.q = q.strip() if isinstance(q, str) and q.strip() else None

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

def paginate(
    session: Session,
    stmt: Select,
    params: PageParams,
    allowed_sort: dict[str, Any] | None = None,
    default_sort: Any | None = None,
) -> tuple[list[Any], int]:
    """Applies count, sort, offset, and limit to a SQLAlchemy Select statement."""
    # Count total rows
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = session.scalar(count_stmt) or 0

    # Apply sorting
    if params.sort and allowed_sort:
        sort_clauses = []
        for part in params.sort.split(","):
            part = part.strip()
            descending = part.startswith("-")
            key = part[1:] if descending else part
            if key not in allowed_sort:
                raise AppError(
                    code="validation_error",
                    message=f"Invalid sort key '{key}'. Allowed: {list(allowed_sort.keys())}",
                    status_code=422,
                )
            col = allowed_sort[key]
            sort_clauses.append(col.desc() if descending else col.asc())
        if sort_clauses:
            stmt = stmt.order_by(*sort_clauses)
    elif default_sort is not None:
        stmt = stmt.order_by(default_sort)

    # Apply pagination offset and limit
    offset = (params.page - 1) * params.page_size
    stmt = stmt.offset(offset).limit(params.page_size)

    items = list(session.scalars(stmt).all())
    return items, total
