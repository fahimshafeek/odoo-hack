from typing import Generic, TypeVar, List, Optional, Dict, Any, Callable
from pydantic import BaseModel
from fastapi import Query
from sqlalchemy import select, func
from sqlalchemy.sql import Select
from app.core.errors import AppError

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        page: int = 1,
        page_size: int = 25,
        sort: Optional[str] = None,
        q: Optional[str] = None,
    ):
        if page < 1:
            raise AppError("validation_error", "Page must be >= 1", 422)
        if page_size < 1 or page_size > 100:
            raise AppError("validation_error", "Page size must be between 1 and 100", 422)
        self.page = page
        self.page_size = page_size
        self.sort = sort
        self.q = q.strip() if q else None


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


def paginate(
    session,
    stmt: Select,
    params: PageParams,
    *,
    allowed_sort: Dict[str, Any],
    default_sort: str = "-created_at",
    map_row: Optional[Callable[[Any], Any]] = None,
) -> Page:
    # 1. Total count
    count_subq = stmt.order_by(None).subquery()
    count_stmt = select(func.count()).select_from(count_subq)
    total = session.execute(count_stmt).scalar() or 0

    # 2. Sorting
    sort_spec = params.sort or default_sort
    order_clauses = []
    for raw_part in sort_spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        desc = part.startswith("-")
        col_name = part[1:] if desc else part
        if col_name not in allowed_sort:
            raise AppError("validation_error", f"Invalid sort field: {col_name}", 422)
        col = allowed_sort[col_name]
        order_clauses.append(col.desc() if desc else col.asc())

    if order_clauses:
        stmt = stmt.order_by(*order_clauses)

    # 3. Limit / Offset
    offset = (params.page - 1) * params.page_size
    stmt = stmt.offset(offset).limit(params.page_size)

    rows = session.execute(stmt).scalars().all()
    if map_row:
        items = [map_row(r) for r in rows]
    else:
        items = list(rows)

    return Page(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
