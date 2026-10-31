# Subscriptions API Reference

Base URL: `http://localhost:8000`  
Authentication: `Authorization: Bearer <JWT>`

## Endpoints

| Method | Path | Allowed Roles | Description |
|---|---|---|---|
| `POST` | `/subscriptions/price-preview` | admin, staff | Compute live preview of unit prices, taxes, and totals |
| `GET` | `/subscriptions` | admin, staff | List subscriptions with pagination, status filters, and search |
| `POST` | `/subscriptions` | admin, staff | Create draft subscription with line snapshots |
| `POST` | `/subscriptions/from-template/{id}` | admin, staff | Create draft subscription from quotation template (D26 defaults) |
| `GET` | `/subscriptions/{id}` | admin, staff | Get subscription detail with lines, totals, and allowed actions |
| `PATCH` | `/subscriptions/{id}` | admin, staff | Update lines/plan (Draft only) or header fields (Draft/Quotation) |
| `DELETE` | `/subscriptions/{id}` | admin, staff | Delete subscription (Draft only) |
| `POST` | `/subscriptions/{id}/transition` | admin, staff | Execute state machine transition (`send_quote`, `confirm`, etc.) |
| `GET` | `/subscriptions/{id}/history` | admin, staff | Get audit history timeline |
| `GET` | `/me/subscriptions` | customer | List customer's own subscriptions (excludes Drafts) |
| `GET` | `/me/subscriptions/{id}` | customer | Get customer's own subscription detail (404 on Draft or other customer) |
| `POST` | `/me/subscriptions/{id}/actions` | customer | Customer action (`pause`, `resume`, `close`, `renew`) |
| `GET` | `/me/subscriptions/{id}/history` | customer | Customer view of own subscription history |

## State Machine Transition Matrix

| From Status | Action | To Status | Guard / Side Effects |
|---|---|---|---|
| `draft` | `send_quote` | `quotation` | >=1 line, plan active, valid start date. Sets `quote_valid_until`. |
| `quotation` | `confirm` | `confirmed` | Confirms quotation. |
| `quotation` | `reject` | `closed` | Rejects quote. |
| `confirmed` | `activate` | `active` | Sets `next_billing_date = start_date`. |
| `active` | `pause` | `paused` | Requires `plan.allow_pause == true`. |
| `paused` | `resume` | `active` | Skips paused periods, advances `next_billing_date` to next cycle >= today (D16). |
| `active` | `renew` | `active` | Extends `expiry_date` by one original term, clears renewal flag (D17). |
| `active` | `close` | `closed` | Requires `plan.allow_early_close == true`. |

## Sample Requests & Responses

### 1. Pricing Preview (PROD-2)
`POST /subscriptions/price-preview`
```json
{
  "plan_id": "99b8cefa-...",
  "lines": [
    {
      "product_id": "e5b8d6fc-...",
      "quantity": 2,
      "variant_value_ids": ["12b8cd9f-..."]
    }
  ]
}
```
Response `200 OK`:
```json
{
  "lines": [
    {
      "product_id": "e5b8d6fc-...",
      "unit_price": "1560.00",
      "amount": "3120.00",
      "tax_rate": "18.00",
      "tax_amount": "561.60",
      "total": "3681.60"
    }
  ],
  "plan_fee": {
    "amount": "2000.00",
    "tax_rate": "18.00",
    "tax_amount": "360.00",
    "total": "2360.00"
  },
  "totals": {
    "subtotal": "5120.00",
    "tax_total": "921.60",
    "total": "6041.60"
  }
}
```
