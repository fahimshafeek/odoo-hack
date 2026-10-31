# Brightloop Subscription Management System
## Member M2 — Catalog & Subscriptions

This repository folder (`M2/`) contains the complete standalone implementation of the **Catalog & Subscriptions** domain for the Brightloop Subscription Management System, built with **Python 3.12 (FastAPI + SQLAlchemy 2.0 + SQLite)** and **Svelte 5 (Vite + Tailwind CSS)**.

---

## 🚀 Quick Start (One Command Run)

### 1. Run the Backend (FastAPI + SQLite)
```bash
cd M2/backend
./run.sh
```
* Or manually:
```bash
cd M2/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py --reset
uvicorn app.main:app --reload --port 8000
```
- API is running at: **http://127.0.0.1:8000**
- Interactive Swagger OpenAPI Docs: **http://127.0.0.1:8000/docs**
- Health check: **http://127.0.0.1:8000/health**

### 2. Run the Frontend (Svelte 5 + Vite + Tailwind CSS)
```bash
cd M2/frontend
npm install
npm run dev
```
- Frontend application runs at: **http://127.0.0.1:5173**

---

## 🧪 Running the Automated Test Suite

Run the full pytest suite (69 tests covering 100% of state transitions, pricing math, billing anchor logic, and catalog CRUD):
```bash
cd M2/backend
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

---

## 📦 What Was Built (Mapped to Requirements)

| Requirement | Description | Implementation File |
|---|---|---|
| **PROD-1** | Product: name, type, sales price, cost price, notes, soft warnings | `app/catalog/models.py`, `app/catalog/service.py` |
| **PROD-2** | Product variants & extra prices (e.g. Brand = Odoo adds ₹560.00) | `app/subscriptions/pricing.py`, `app/catalog/router.py` |
| **PLAN-1** | Plan: price, billing period (daily/weekly/monthly/yearly), min qty, validity dates | `app/catalog/models.py`, `app/catalog/schemas.py` |
| **PLAN-2** | Per-plan rules: auto_close, allow_early_close, allow_pause, allow_renew | `app/subscriptions/state.py` |
| **SUB-1** | Quotation templates (plan + lines + validity days) | `app/catalog/service.py`, `app/catalog/router.py` |
| **SUB-2** | Subscription: numbering sequence (`SUB-{year}-{seq:06d}`), customer, plan, dates | `app/core/numbering.py`, `app/subscriptions/service.py` |
| **SUB-3** | Subscription lines: product, variant snapshot, unit price, taxes, line amounts | `app/subscriptions/models.py`, `app/subscriptions/service.py` |
| **SUB-4** | Status flow Draft → Quotation → Confirmed → Active → Paused / Closed | `app/subscriptions/state.py` |
| **EXTRA** | Renewals action (extends expiry by one term) & upcoming renewals flag | `app/subscriptions/state.py`, `app/subscriptions/jobs.py` |
| **Gate G6** | Billing support interfaces for M3 (`add_period`, `next_period`, `count_due`, `due_subscriptions`) | `app/subscriptions/billing_support.py` |
| **D16** | Resume skips paused periods without invoicing and sets next billing date | `app/subscriptions/state.py` |
| **D21** | Customer portal scoping (customers see own non-draft data, 404 on probing) | `app/core/deps.py`, `app/subscriptions/portal_router.py` |
| **D26** | Create subscription from quotation template with sensible defaults | `app/subscriptions/service.py` |

---

## 📂 Architecture & Folder Structure

```
M2/
├── backend/
│   ├── app/
│   │   ├── core/                  # Clock, Money (Decimal q2), Errors, Pagination, Security, Numbering
│   │   ├── catalog/               # Tax, Product, Variant, Plan, PaymentTerm, QuotationTemplate
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── subscriptions/         # Lifecycle, State machine, Pricing, Billing support, Scheduled jobs
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── pricing.py
│   │   │   ├── billing_support.py
│   │   │   ├── state.py
│   │   │   ├── jobs.py
│   │   │   ├── service.py
│   │   │   ├── router.py
│   │   │   └── portal_router.py
│   │   ├── main.py                # FastAPI app with CORS and error handlers
│   │   └── worker.py              # Lifecycle jobs runner (--once activate_due / all)
│   ├── scripts/
│   │   ├── seed.py                # Database seed orchestrator
│   │   └── seed_parts/
│   │       └── catalog_subs.py    # Demo data seed (~12 products, 5 plans, ~30 subscriptions)
│   ├── tests/                     # 69 pytest tests (100% green)
│   ├── requirements.txt
│   └── run.sh
├── frontend/                      # Svelte 5 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── lib/                   # API client, types, formatters
│   │   ├── components/            # ProductsView, PlansView, PaymentTermsView,
│   │   │                          # QuotationTemplatesView, SubscriptionsView, PriceCalculator
│   │   ├── App.svelte
│   │   └── main.ts
│   └── package.json
└── docs/
    ├── modules/
    │   └── catalog-subscriptions.md
    └── api/
        ├── catalog.md
        └── subscriptions.md
```
