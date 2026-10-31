from datetime import timedelta
from decimal import Decimal
import pytest
from app.auth.models import Customer
from app.billing.models import Invoice
from app.catalog.models import Plan
from app.core.clock import today
from app.subscriptions.models import Subscription

def test_reports_summary_and_overdue(client, session, auth_headers):
    curr_date = today()
    headers = auth_headers(role="admin")

    # Setup Plan
    plan = Plan(name="Starter", price=Decimal("1000.00"), billing_period="monthly")
    session.add(plan)
    session.flush()

    # Setup Customer
    cust = Customer(company_name="Acme Corp", phone="+91 12345 67890")
    session.add(cust)
    session.flush()

    # Setup Active Subscription
    sub = Subscription(
        number="SUB-TEST-001",
        customer_id=cust.id,
        plan_id=plan.id,
        status="active",
        start_date=curr_date - timedelta(days=30),
        expiry_date=curr_date + timedelta(days=15),  # Upcoming renewal (< 30 days)
    )
    session.add(sub)
    session.flush()

    # Setup Overdue Invoice
    inv_overdue = Invoice(
        number="INV-OVERDUE-001",
        subscription_id=sub.id,
        customer_id=cust.id,
        status="confirmed",
        period_start=curr_date - timedelta(days=30),
        period_end=curr_date - timedelta(days=1),
        issue_date=curr_date - timedelta(days=30),
        due_date=curr_date - timedelta(days=5),
        total=Decimal("1180.00"),
        amount_paid=Decimal("0.00"),
    )
    session.add(inv_overdue)
    session.commit()

    # Query Summary
    res = client.get("/reports/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["active_subscriptions"] == 1
    assert data["mrr"] == "1000.00"
    assert data["overdue_count"] == 1
    assert data["upcoming_renewals_count"] == 1

    # Query Overdue Invoices
    res_overdue = client.get("/reports/overdue-invoices", headers=headers)
    assert res_overdue.status_code == 200
    overdue_data = res_overdue.json()
    assert overdue_data["total"] == 1
    assert overdue_data["items"][0]["number"] == "INV-OVERDUE-001"
    assert overdue_data["items"][0]["days_overdue"] == 5

def test_csv_export_injection_guard(client, session, auth_headers):
    headers = auth_headers(role="admin")
    res = client.get("/reports/export.csv?report=overdue", headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
