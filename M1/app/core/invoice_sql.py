from datetime import date
from sqlalchemy import and_, column, table

# Standalone lightweight table representation so M1 and M3 don't circularly import models
invoices_t = table(
    "invoices",
    column("id"),
    column("number"),
    column("subscription_id"),
    column("customer_id"),
    column("status"),
    column("issue_date"),
    column("due_date"),
    column("total"),
    column("amount_paid"),
    column("created_at"),
)

def balance_expr(inv_table=invoices_t):
    """Derived balance expression: total - amount_paid."""
    return inv_table.c.total - inv_table.c.amount_paid

def is_overdue_expr(today_date: date, inv_table=invoices_t):
    """Invoice is overdue: Confirmed, balance > 0, and due_date < today."""
    return and_(
        inv_table.c.status == "confirmed",
        inv_table.c.due_date < today_date,
        balance_expr(inv_table) > 0,
    )

def payment_filter_clause(filter_type: str, today_date: date, inv_table=invoices_t):
    """Returns the SQL clause for paid / outstanding / overdue filters."""
    if filter_type == "paid":
        return inv_table.c.status == "paid"
    if filter_type == "outstanding":
        return and_(
            inv_table.c.status == "confirmed",
            balance_expr(inv_table) > 0,
        )
    if filter_type == "overdue":
        return is_overdue_expr(today_date, inv_table)
    return True
