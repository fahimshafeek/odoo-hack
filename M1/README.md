# Brightloop Subscription Management System — M1: Platform, Auth & Reports

Backend architecture and services for identity, role-based access control (RBAC), and real-time financial reporting for Brightloop Software.

---

## 1. Quick Start

### 1.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.2 Environment Configuration
Copy `.env.example` to `.env` (already done locally; `.env` is strictly git-ignored):
```bash
cp .env.example .env
```
Key settings configured in `.env`:
* `DATABASE_URL=sqlite:///./brightloop.db` (SQLite with WAL mode, 5s busy timeout, foreign keys enabled)
* `PASSWORD_RESET_EXPIRE_MINUTES=5` (Password reset links expire in 5 minutes)
* `RESEND_API_KEY=...` (Outbound email delivery for reset links and invitations)
* `EMAIL_FROM=Hari <hakku@mail.laddu.cc>`

### 1.3 Seed the Database
Populates demo accounts, sample subscriptions, invoices, and payments:
```bash
python -m scripts.seed --reset
```

Default credentials:
* **Admin:** `admin@brightloop.test` / `BrightloopAdmin@123`
* **Staff:** `staff@brightloop.test` / `BrightloopStaff@123`
* **Customer:** `customer@brightloop.test` / `BrightloopCust@123`

### 1.4 Start the FastAPI Server
```bash
uvicorn app.main:app --reload --port 8000
```
* **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
* **Alternative ReDoc UI:** `http://localhost:8000/redoc`

---

## 2. Testing & Quality Assurance

Run the automated test suite covering password complexity, duplicate email handling, token lifecycle, RBAC isolation, and reporting KPIs:
```bash
python -m pytest -v
```

---

## 3. Implemented API Surface

### 3.1 Authentication & Profile (`/auth`, `/me`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | Public | Customer registration with $\ge 9$ char regex password validator. Returns JWT. |
| `POST` | `/auth/login` | Public | Login with brute-force rate limiter (5 attempts/min). Returns JWT. |
| `GET` | `/auth/me` | Authenticated | Profile & role information of the current user. |
| `POST` | `/auth/forgot-password` | Public | Generates single-use token and sends 5-minute reset link via Resend API. |
| `POST` | `/auth/reset-password` | Public | Updates password using valid, unexpired token. |
| `GET` | `/me/profile` | Customer | View customer's own company profile (IDOR protected). |
| `PATCH` | `/me/profile` | Customer | Update customer's company name, phone, billing address, tax ID. |

### 3.2 Staff & Customer Management (`/staff`, `/customers`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/staff` | Admin Only | Add internal staff; sends 24h setup invite email via Resend. |
| `GET` | `/staff` | Admin Only | Paginated list of staff members with search. |
| `PATCH` | `/staff/{id}` | Admin Only | Update staff name or deactivate account. |
| `GET` | `/customers` | Admin & Staff | Paginated list of registered customers with fuzzy search. |
| `POST` | `/customers` | Admin & Staff | Create a customer manually and send invitation email. |
| `GET` | `/customers/{id}` | Admin & Staff | Retrieve customer profile details. |

### 3.3 Executive Finance Reports (`/reports`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/reports/summary` | Admin & Staff | Summary KPI cards: Active subscriptions, MRR, Collected revenue, Invoiced total, Outstanding balance, Overdue count. (30s in-memory cache) |
| `GET` | `/reports/revenue-by-month` | Admin & Staff | 12-month invoiced vs collected revenue for frontend charts. |
| `GET` | `/reports/overdue-invoices` | Admin & Staff | Paginated overdue invoices with customer phone and days overdue for chasing. |
| `GET` | `/reports/upcoming-renewals` | Admin & Staff | Active subscriptions expiring within the next 30 days. |
| `GET` | `/reports/export.csv` | Admin & Staff | Streaming CSV download with spreadsheet formula-injection protection (`=`, `+`, `-`, `@`). |

---

## 4. Teammate Router Placeholders

To ensure your teammates (**M2**, **M3**, **M4**) can collaborate without merge conflicts, router stubs are already mounted in `app/main.py`:
* `app/catalog/router.py` (M2: Products & Plans)
* `app/subscriptions/router.py` (M2: Subscriptions & Quotes)
* `app/billing/router.py` (M3: Invoices, Taxes & Discounts)
* `app/payments/router.py` (M3: Payments ledger)

Teammates can expand their routers directly without modifying `app/main.py` or `app/core/`.
