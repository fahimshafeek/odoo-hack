"""
Concurrency race condition tests for M3 (B3 3.3, B4).
Uses temporary SQLite database file with WAL mode and thread barriers
for clean, isolated multi-threading verification.
"""

import os
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core_compat import AppError, today
from app.database import Base
from app.discounts import claim_discount_usage_atomic
from app.models import Discount, Invoice
from app.payments import record_payment
from app.schemas import PaymentCreate


@pytest.fixture
def file_db_factory():
    tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_file.close()
    db_url = f"sqlite:///{tmp_file.name}"
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False, "timeout": 30.0}
    )

    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield session_factory

    Base.metadata.drop_all(engine)
    engine.dispose()
    if os.path.exists(tmp_file.name):
        try:
            os.unlink(tmp_file.name)
        except OSError:
            pass


def test_concurrent_discount_limit_race(file_db_factory):
    """
    Race test from prompt:
    8 threads create/claim concurrently with usage_limit=3 -> exactly 3 succeed, used_count == 3.
    """
    curr_date = today()
    init_session = file_db_factory()
    disc = Discount(
        name="Flash 3 Limit",
        type="percent",
        value=Decimal("10.00"),
        scope="subscription",
        usage_limit=3,
        used_count=0,
        start_date=curr_date,
        end_date=curr_date,
        is_active=True,
    )
    init_session.add(disc)
    init_session.commit()
    disc_id = disc.id
    init_session.close()

    barrier = threading.Barrier(8)
    results: list[bool] = []
    lock = threading.Lock()

    def worker():
        barrier.wait()
        session = file_db_factory()
        try:
            success = claim_discount_usage_atomic(session, disc_id)
            session.commit()
            with lock:
                results.append(success)
        except Exception:
            session.rollback()
            with lock:
                results.append(False)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker) for _ in range(8)]
        for f in futures:
            f.result()

    successful_claims = [r for r in results if r is True]
    assert len(successful_claims) == 3

    check_session = file_db_factory()
    reloaded = check_session.get(Discount, disc_id)
    assert reloaded.used_count == 3
    check_session.close()


def test_concurrent_payment_overpayment_race(file_db_factory, admin_user):
    """
    Race test from prompt:
    Two concurrent payments each of 60% of balance -> exactly one succeeds,
    second gets rejected as overpayment (422).
    """
    curr_date = today()
    init_session = file_db_factory()
    inv = Invoice(
        number="INV-2026-PAYRACE",
        subscription_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status="confirmed",
        period_start=curr_date,
        period_end=curr_date,
        issue_date=curr_date,
        due_date=curr_date,
        total=Decimal("100.00"),
        amount_paid=Decimal("0.00"),
    )
    init_session.add(inv)
    init_session.commit()
    inv_id = inv.id
    init_session.close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def pay_worker():
        barrier.wait()
        session = file_db_factory()
        try:
            record_payment(
                session,
                inv_id,
                PaymentCreate(method="card", amount=Decimal("60.00")),
                admin_user,
            )
            session.commit()
            with lock:
                outcomes.append("success")
        except AppError as ae:
            session.rollback()
            with lock:
                outcomes.append(f"error:{ae.code}")
        except Exception:
            session.rollback()
            with lock:
                outcomes.append("error:conflict")
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(pay_worker)
        f2 = executor.submit(pay_worker)
        f1.result()
        f2.result()

    assert "success" in outcomes
    assert outcomes.count("success") == 1
    assert "error:overpayment" in outcomes or "error:conflict" in outcomes

    check_session = file_db_factory()
    reloaded = check_session.get(Invoice, inv_id)
    assert reloaded.amount_paid == Decimal("60.00")
    check_session.close()
