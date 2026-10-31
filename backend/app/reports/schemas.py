from datetime import date
import uuid
from pydantic import BaseModel

class ReportSummaryOut(BaseModel):
    as_of: date
    active_subscriptions: int
    mrr: str
    revenue_collected: str
    invoiced_total: str
    outstanding_total: str
    overdue_count: int
    overdue_total: str
    upcoming_renewals_count: int

class MonthlyRevenueItem(BaseModel):
    month: str       # YYYY-MM
    invoiced: str
    collected: str

class OverdueInvoiceItem(BaseModel):
    invoice_id: uuid.UUID | str
    number: str
    customer_id: uuid.UUID | str
    customer_name: str
    phone: str | None
    due_date: date
    days_overdue: int
    total: str
    balance: str

class UpcomingRenewalItem(BaseModel):
    subscription_id: uuid.UUID | str
    number: str
    customer_name: str
    plan_name: str
    expiry_date: date
    days_left: int
    allow_renew: bool
