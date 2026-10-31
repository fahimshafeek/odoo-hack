from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.db import get_session
from app.core.deps import AuthUser, require_role
from app.core.pagination import Page, PageParams
from app.reports.schemas import (
    MonthlyRevenueItem,
    OverdueInvoiceItem,
    ReportSummaryOut,
    UpcomingRenewalItem,
)
from app.reports.service import (
    export_csv_stream,
    get_overdue_invoices,
    get_reports_summary,
    get_revenue_by_month,
    get_upcoming_renewals,
)

router = APIRouter(tags=["reports"])
portal_router = APIRouter(tags=["portal_reports"])

@router.get("/reports/summary", response_model=ReportSummaryOut)
def report_summary(
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session)
):
    """Executive summary KPI cards (Active subs, MRR, Invoiced, Collected, Overdue)."""
    return get_reports_summary(session)

@router.get("/reports/revenue-by-month", response_model=list[MonthlyRevenueItem])
def report_revenue_by_month(
    months: int = Query(12, ge=1, le=36),
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session)
):
    """Monthly breakdown of invoiced vs collected revenue for charts."""
    return get_revenue_by_month(session, months=months)

@router.get("/reports/overdue-invoices", response_model=Page[OverdueInvoiceItem])
def report_overdue_invoices(
    params: PageParams = Depends(),
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session)
):
    """List of overdue invoices with customer phone and balance for chasing."""
    items, total = get_overdue_invoices(session, params)
    return Page[OverdueInvoiceItem](
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )

@router.get("/reports/upcoming-renewals", response_model=Page[UpcomingRenewalItem])
def report_upcoming_renewals(
    params: PageParams = Depends(),
    days: int = Query(30, ge=1, le=90),
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session)
):
    """Subscriptions expiring within the next 30 days."""
    items, total = get_upcoming_renewals(session, params, days=days)
    return Page[UpcomingRenewalItem](
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )

@router.get("/reports/export.csv")
def report_export_csv(
    report: str = Query("overdue", description="overdue | upcoming_renewals | subscriptions"),
    current_user: AuthUser = Depends(require_role("admin", "staff")),
    session: Session = Depends(get_session)
):
    """Streams a CSV export with formula injection protection."""
    csv_stream = export_csv_stream(session, report)
    filename = f"brightloop_{report}_report.csv"
    return StreamingResponse(
        iter([csv_stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
