# M3: Billing & Payments API Documentation

This document describes the REST API endpoints implemented in `M3/` for the Brightloop Subscription Management System.

---

## 1. Taxes (INV-2)

### `GET /taxes`
- **Role**: Admin, Staff
- **Query params**: `active: bool = False`
- **Response**: `200 OK` `list[TaxOut]`

### `POST /taxes`
- **Role**: Admin
- **Body**: `{ "name": string (<=60), "rate_percent": string ("18.00"), "is_active": bool }`
- **Response**: `201 Created` `TaxOut`

### `PATCH /taxes/{tax_id}`
- **Role**: Admin
- **Body**: `{ "name"?: string, "rate_percent"?: string, "is_active"?: bool }`
- **Response**: `200 OK` `TaxOut`

### `DELETE /taxes/{tax_id}`
- **Role**: Admin
- **Behavior**: Deactivates (`is_active = False`) if referenced by invoice lines; hard-deletes otherwise.
- **Response**: `204 No Content`

---

## 2. Discounts (DISC-1, DISC-2, DISC-3, D19)

### `GET /discounts`
- **Role**: Admin, Staff
- **Response**: `200 OK` `list[DiscountOut]`

### `GET /discounts/{id}`
- **Role**: Admin, Staff
- **Response**: `200 OK` `DiscountOut`

### `POST /discounts`
- **Role**: Admin
- **Body**:
  ```json
  {
    "name": "Summer Launch 10%",
    "type": "percent",
    "value": "10.00",
    "scope": "subscription",
    "min_purchase": "500.00",
    "min_quantity": 2,
    "start_date": "2026-10-01",
    "end_date": "2026-11-30",
    "usage_limit": 50,
    "is_active": true,
    "targets": []
  }
  ```
- **Response**: `201 Created` `DiscountOut`

### `PATCH /discounts/{id}`
- **Role**: Admin
- **D19 Edit-Lock Rule**: If `used_count > 0`, attempts to modify `type`, `value`, `scope`, or `targets` return `409 conflict`.
- **Response**: `200 OK` `DiscountOut`

### `DELETE /discounts/{id}`
- **Role**: Admin
- **Behavior**: Deactivates if `used_count > 0`; deletes otherwise.
- **Response**: `204 No Content`

---

## 3. Invoices (INV-1, INV-3, INV-4, PAY-3)

### `GET /invoices`
- **Role**: Admin, Staff
- **Filters**:
  - `status`: `draft` | `confirmed` | `paid` | `cancelled`
  - `payment_filter`: `paid` | `outstanding` (confirmed with balance > 0) | `overdue` (confirmed, balance > 0, due_date < today)
  - `customer_id`: UUID
  - `subscription_id`: UUID
  - `date_from`, `date_to`: ISO dates
  - `q`: search by invoice number
  - `page`, `page_size`: pagination
- **Response**: `200 OK` `{ "items": [InvoiceListItem], "total": int, "page": int, "page_size": int }`

### `GET /invoices/{id}`
- **Role**: Admin, Staff (Customer: own confirmed/paid only, else 404)
- **Response**: `200 OK` `InvoiceDetail`

### `POST /invoices/{id}/confirm`
- **Role**: Admin, Staff
- **Behavior**: Transitions Draft &rarr; Confirmed. If `total == 0.00`, transitions immediately to Paid (D20).
- **Response**: `200 OK` `InvoiceDetail`

### `POST /invoices/{id}/cancel`
- **Role**: Admin, Staff
- **Behavior**:
  - Draft &rarr; Cancelled: releases discount usage (decrements `used_count`, deletes redemptions).
  - Confirmed &rarr; Cancelled: allowed only if `amount_paid == 0`.
- **Response**: `200 OK` `InvoiceDetail`

### `POST /invoices/{id}/send`
- **Role**: Admin, Staff
- **Behavior**: Generates PDF, emails customer, sets `sent_at = now()`.
- **Response**: `200 OK` `InvoiceDetail`

### `GET /invoices/{id}/pdf`
- **Role**: Admin, Staff, Customer (own non-draft)
- **Response**: `200 OK` with `Content-Type: application/pdf`

---

## 4. Billing Runs (INV-5)

### `POST /billing/run`
- **Role**: Admin, Staff
- **Body**: `{ "as_of": "2026-10-31" }` (optional, defaults to today)
- **Behavior**: Executes batch billing run. Idempotent: safe to run multiple times.
- **Response**: `202 Accepted` `{ "billing_run_id": UUID, "status": "running" }`

### `GET /billing/runs`
- **Role**: Admin, Staff
- **Response**: `200 OK` Paginated history of runs.

### `GET /billing/runs/{id}`
- **Role**: Admin, Staff
- **Response**: `200 OK` `BillingRunOut`

---

## 5. Payments (PAY-1, PAY-2, D27)

### `POST /invoices/{id}/payments`
- **Role**: Admin, Staff
- **Body**: `{ "method": "card"|"upi"|"bank_transfer"|"cash"|"cheque"|"online", "amount": "250.00", "paid_on"?: date, "note"?: string }`
- **Guards**: `amount <= balance` (rejects overpayment with 422). Auto-flips invoice status to Paid when balance hits 0.
- **Response**: `201 Created` `PaymentOut`

### `GET /payments`
- **Role**: Admin, Staff
- **Response**: `200 OK` `list[PaymentOut]`

---

## 6. Customer Portal (`/me/...`)

- `GET /me/invoices`: List own confirmed/paid invoices.
- `GET /me/invoices/{id}`: View own invoice detail.
- `GET /me/invoices/{id}/pdf`: Download own invoice PDF.
- `POST /me/invoices/{id}/pay`: Mock online payment (`D27`).
- `GET /me/payments`: List own payment history.
