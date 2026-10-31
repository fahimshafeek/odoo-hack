from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
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
        page_size: int = Query(25, ge=1, le=100, description="Items per page"),
        sort: Optional[str] = Query(None, description="Sort fields, comma-separated with - for desc"),
        q: Optional[str] = Query(None, description="Search query"),
    ):
        self.page = page if isinstance(page, int) else 1
        self.page_size = page_size if isinstance(page_size, int) else 25
        if self.page < 1:
            raise AppError("validation_error", "Page must be >= 1", 422)
        if self.page_size < 1 or self.page_size > 1000:
            raise AppError("validation_error", "Page size must be between 1 and 1000", 422)
        self.sort = sort if isinstance(sort, str) else None
        self.q = q.strip() if isinstance(q, str) and q.strip() else None


def page_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Sort fields, comma-separated with - for desc"),
    q: Optional[str] = Query(None, description="Search query"),
) -> PageParams:
    return PageParams(page=page, page_size=page_size, sort=sort, q=q)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    def __iter__(self):
        """Allows unpacking as `items, total = paginate(...)` for M1 compatibility."""
        yield self.items
        yield self.total


def paginate(
    session: Session,
    stmt: Select,
    params: PageParams,
    allowed_sort: Optional[Dict[str, Any]] = None,
    default_sort: Any = "-created_at",
    map_row: Optional[Callable[[Any], Any]] = None,
) -> Page:
    """Applies count, sort, offset, and limit to a SQLAlchemy Select statement."""
    # Count total rows
    count_subq = stmt.order_by(None).subquery()
    count_stmt = select(func.count()).select_from(count_subq)
    total = session.scalar(count_stmt) or 0

    # Apply sorting
    sort_spec = params.sort if params.sort else (default_sort if isinstance(default_sort, str) else None)
    if sort_spec and allowed_sort:
        sort_clauses = []
        for part in sort_spec.split(","):
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
    elif default_sort is not None and not isinstance(default_sort, str):
        stmt = stmt.order_by(default_sort)

    # Offset & limit
    offset = (params.page - 1) * params.page_size
    stmt = stmt.offset(offset).limit(params.page_size)

    rows = session.scalars(stmt).all()
    items = [map_row(r) for r in rows] if map_row else list(rows)

    return Page(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
