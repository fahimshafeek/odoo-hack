# Brightloop — M2: Catalog & Subscriptions Walkthrough

## 1. What This Module Does
The **Catalog & Subscriptions** module owns "what we sell and to whom":
- **Products & Variants (PROD-1, PROD-2):** Products with sales price, cost price, and customizable attributes (e.g. Brand = Odoo adds ₹560.00). Live soft warnings when cost price exceeds sales price.
- **Subscription Plans (PLAN-1, PLAN-2):** Billing periods (`daily`, `weekly`, `monthly`, `yearly`), minimum quantities, validity windows, and four binding lifecycle rule flags (`allow_pause`, `allow_renew`, `allow_early_close`, `auto_close`).
- **Quotation Templates (SUB-1):** Reusable quote templates with validity periods and line item bundles.
- **Subscriptions & State Machine (SUB-2, SUB-3, SUB-4):** Sequential document numbering (`SUB-{year}-{seq:06d}`), full lifecycle state transitions (`Draft → Quotation → Confirmed → Active → Paused / Closed`), plan rule enforcement, and complete audit history logs.
- **Billing Support (Gate G6 for M3):** Pure period anchor calculation (`31 Jan → 28 Feb → 31 Mar`), due subscription queries, and concurrency-safe billing date advancement.
- **Scheduled Lifecycle Jobs:** Automatic activation of due subscriptions, automatic quote expiry, auto-close of expired subscriptions, and upcoming renewal flagging.

---

## 2. The Three Hardest Decisions & Solutions

### Decision 1: Month-End Anchor Date Preservation (`add_period`)
- **Challenge:** Subscriptions starting on January 31st must bill on February 28th (or 29th on leap years) and then resume on March 31st, not March 28th.
- **Solution:** Implemented pure function `add_period(d, period, anchor_day)` that captures `anchor_day = sub.start_date.day`. Clamps to month end if the target month has fewer days, but restores the original anchor day in longer months.

### Decision 2: Plan Flag Invariance across All Roles
- **Challenge:** In many systems, admin users accidentally bypass business rules (such as pausing a plan where pause is forbidden).
- **Solution:** In `subscriptions/state.py::transition`, plan rule flags (`plan.allow_pause`, `plan.allow_renew`, `plan.allow_early_close`) strictly bind everyone, including admins. Customer users are additionally restricted to only `pause`, `resume`, `close`, `renew` on their own subscriptions.

### Decision 3: Deterministic Price Preview and Snapshot Separation
- **Challenge:** Avoid divergence between form price previews and database persisted line items.
- **Solution:** Unified pricing in `subscriptions/pricing.py`. The price-preview endpoint (`POST /subscriptions/price-preview`) and the persistence layer (`create_subscription`) share the identical pure functions (`resolve_variant`, `unit_price`, `line_amount`).

---

## 3. How to Demo (2-Minute Demo Script)
1. **Catalog & Variants (PROD-2):**
   - Open Products view. Show `Odoo ERP` (Base ₹1,000.00).
   - Click "Pricing Preview" in the navbar.
   - Select `Odoo ERP` with `Brand: Odoo (+₹560.00)`.
   - Show unit price immediately computes to **₹1,560.00**. Show GST (18%) and total **₹1,840.80**.
2. **Quotation from Template (D26, SUB-1):**
   - Click "New Subscription" → choose "SME Standard ERP Starter".
   - Generates a Draft subscription with lines copied and snapshot prices preserved.
3. **State Stepper & Lifecycle (SUB-4):**
   - Open the created Draft subscription.
   - Click **Send Quote** → status becomes `Quotation`, validity date set.
   - Click **Confirm** → status becomes `Confirmed`.
   - Click **Activate** → status becomes `Active`, `next_billing_date` set to `start_date`.
   - Click **Pause** → status becomes `Paused`.
   - Click **Resume** → skips paused periods and sets `next_billing_date` to next cycle.
   - Show Audit History timeline recording every transition and note.
4. **Customer Portal Scoping (D21):**
   - Switch role to **Customer** in top navigation.
   - Demonstrates that Drafts are hidden and customer can only view and act on their own data.

---

## 4. What If X Fails?
- **What if worker drops offline for 3 days?**
  Catch-up logic advances `next_billing_date` and `advance_next_billing_date` ensures all missed periods are processed sequentially without skipping.
- **What if a customer tries to access another customer's subscription?**
  Returns HTTP `404 Not Found` (never 403), preventing attackers from probing subscription IDs.
- **What if an attribute value from another product is submitted?**
  `resolve_variant` rejects foreign IDs with HTTP `422 validation_error`.
