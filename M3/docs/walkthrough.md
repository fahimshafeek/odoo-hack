# M3: Billing & Payments — Module Walkthrough

**Module Owner:** M3 (Billing & Payments)  
**Database:** SQLite (`M3/billing.db` / WAL mode)  
**Framework:** FastAPI (Python 3.12+ / 3.13) with SQLAlchemy 2.0 and Pydantic v2  

---

## 1. What M3 Does

M3 is the financial core of the Brightloop Subscription Management System:
1. **Tax Engine (INV-2)**: Accurately computes half-up quantized tax strictly on net amounts (after discounts) per line item.
2. **Discount Engine (DISC-1, DISC-2, DISC-3, D19)**: Manages fixed and percent discounts across product and subscription scopes. Enforces minimum purchase/quantity thresholds, best single discount selection per line, and an atomic 5-round claim loop.
3. **Idempotent Billing Run (INV-1, INV-5)**: Orchestrates automated invoice generation. Guarantees "never billed twice, never skipped" through database constraints (`UNIQUE(subscription_id, period_start)`), multi-period catch-up loops, and savepoint rollbacks.
4. **Invoice State Machine (INV-4, D20)**: Implements lifecycle transitions (`Draft` &rarr; `Confirmed` &rarr; `Paid` or `Cancelled`) with discount usage release on draft cancellation and immediate transition to Paid for zero-total invoices.
5. **Payment Processing (PAY-1, PAY-2, D27)**: Records payments with atomic overpayment prevention, auto-settles invoices to `Paid` upon reaching zero balance, and supports customer portal mock online payments.
6. **PDF & Email (INV-3)**: Generates compliant PDF invoices starting with `%PDF` and dispatches notifications with attachments.

---

## 2. The 3 Hardest Decisions & Architectural Guarantees

### A. "Never Billed Twice, Never Skipped"
- **The Guarantee**: A subscription cannot be billed twice for the same period, nor can any due period be silently dropped.
- **The Mechanism**:
  1. The `invoices` table enforces `UNIQUE(subscription_id, period_start)`.
  2. Each subscription billing step runs inside a database savepoint (`session.begin_nested()`).
  3. If a race or rerun attempts to insert an invoice for an already-billed period, an `IntegrityError` triggers savepoint rollback (undoing any claimed discounts). The engine safely catches this, advances `next_billing_date` past the duplicate period, and counts it as `skipped`.
  4. If an unexpected runtime failure occurs, the savepoint rolls back, `failed` is counted, the subscription ID is isolated, and the billing date does NOT advance, ensuring it will be retried on the next run.
  5. Multi-period catch-up: if a daily plan was offline for 3 days, a single run generates 3 catch-up invoices with contiguous periods.

### B. Atomic Discount Claim Loop (D19)
- **The Race Problem**: Multiple concurrent billing runs or invoice creations could claim a limited discount (e.g., `usage_limit = 3`) simultaneously and exceed the limit.
- **The Solution**: An atomic SQL update:
  ```sql
  UPDATE discounts 
  SET used_count = used_count + 1 
  WHERE id = :id AND (usage_limit IS NULL OR used_count < usage_limit);
  ```
  If `rowcount == 0`, the discount was exhausted by a competing transaction. The engine drops that candidate and re-evaluates (up to 5 rounds). Proven by test `test_concurrent_discount_limit_race` with 8 concurrent threads.

### C. Tax Computed Strictly AFTER Discount
- Tax is calculated on the net line amount (`gross - discount`), per line, quantized half-up.
- For subscription-level fixed discounts, the discount is allocated proportionally across eligible lines based on gross amounts:
  ```python
  line_discount = q2(total_discount * (line_gross / eligible_subtotal))
  ```
  The last eligible line absorbs any rounding remainder, guaranteeing that the sum of line discounts equals the total discount to the exact cent.

---

## 3. How to Demo M3

### Step 1: Run the Seed Script
Populates demo taxes, discounts, active subscriptions, past invoices, and payments:
```bash
PYTHONPATH=. ../.venv/bin/python3 app/seed.py
```
Output:
```
Seeded successfully: {'taxes': 3, 'discounts': 4, 'subscriptions': 3, 'invoices': 4}
```

### Step 2: Verify the Lifecycle States in the Database
```bash
PYTHONPATH=. ../.venv/bin/python3 -c "
from app.database import SessionLocal
from app.models import Invoice
from app.state import derive_payment_state

with SessionLocal() as s:
    for i in s.query(Invoice).all():
        p_state = derive_payment_state(i)
        print(f'{i.number}: status={i.status}, total={i.total}, paid={i.amount_paid}, balance={i.total-i.amount_paid}, payment_state={p_state}')
"
```
Displays:
- `INV-2026-000001`: `status=paid, balance=0.00, payment_state=paid`
- `INV-2026-000002`: `status=confirmed, paid=500.00, balance=3453.00, payment_state=overdue`
- `INV-2026-000003`: `status=confirmed, paid=0.00, balance=1327.50, payment_state=unpaid` (outstanding)
- `INV-2026-000004`: `status=cancelled, payment_state=not_applicable`

### Step 3: Demonstrate Idempotency ("Run Billing Now")
Run billing twice:
```bash
PYTHONPATH=. ../.venv/bin/python3 -c "
from app.database import SessionLocal
from app.engine import run_billing
run_billing(SessionLocal)
run_billing(SessionLocal)
"
```
The first run bills the due-today subscription (`created_count = 1`). The immediate second run creates `0` duplicates (`total_due = 0, created_count = 0`).

### Step 4: Run the Complete Automated Test Suite
```bash
PYTHONPATH=. ../.venv/bin/pytest tests/ -v
```
All **28 tests pass**:
- `test_tax.py`: standard rate, 0%, 100%, half-up edge cases
- `test_calc.py`: hand-computed fixture, tax after discount, proportional allocation
- `test_discounts.py`: eligibility, min purchase/quantity, atomic claim, D19 edit-lock
- `test_state.py`: confirm, cancel, zero-total auto-paid, draft discount release
- `test_payments.py`: partial payment, overpayment rejection, auto-settle to paid, mock pay
- `test_engine.py`: idempotency, 3-day catch-up, pause/close exclusions
- `test_concurrency.py`: 8-thread discount race, concurrent overpayment race
- `test_api.py`: full FastAPI endpoints, RBAC, customer portal scoping
