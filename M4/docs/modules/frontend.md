# M4 frontend walkthrough

The frontend lives in `M4/frontend`: SvelteKit and JavaScript, Tailwind tokens,
shadcn-svelte components, GSAP, and the shared OpenAPI client. The backend uses
SQLite; M4 does not implement billing maths or database access.

## Shared API

Import components from `#lib/components/index.js`. Columns use `{key, header,
cell?, sortKey?}`; `cell` and `mobileCard` are Svelte snippets receiving the row.
DataTable receives a server page and emits pagination/filter patches. It never
sorts or slices business records locally. `useListParams()` exposes a reactive
`.value` and `.update(patch)`; filters reset the page and persist in the URL.

Create forms with `createForm({schema, initialValues})` from
`#lib/forms/form.js`, then pass the instance and an async `onSubmit` to `Form`.
Fields take `name`, `label`, `hint`, and `required`; dotted names support line
editors. `$form.isValid` and `$form.isSubmitting` control submission. The shared
Zod primitives live in `#lib/validators.js`. Server errors remain on their field
until it changes; unknown fields become an alert. `applyServerErrors` is exported.
ComboboxField expects `loadOptions(q)` returning `{value,label}[]`; stale results
are ignored. Use `initialLabel` when an edited record is outside the current page.

Money stays a decimal string through input and validation. `formatMoney` and
MoneyCell only format; prices, taxes, discounts, balances, and permissions come
from the API. StatusBadge has one mapping and always pairs text with an icon.
`notify` supplies mutation toasts, ConfirmDialog handles asynchronous failures,
and `openPdf` uses the shared authenticated client with a short-lived blob URL.

## Three decisions to explain

1. SvelteKit handles navigation; feature manifests keep team ownership intact.
2. Form instances live in component context, so independent forms do not share
   state. Repeated submissions are rejected while a request is running.
3. Motion uses scoped GSAP attachments with cleanup and reduced-motion support.
   The design system, loading, empty, and error states work without animation.

## Demo and failure handling

Run `npm run dev:preview`, then open `/app/subscriptions`. Create a draft, inspect
its lines and history, open `/app/invoices`, record partial/full sample payments,
and run billing twice at `/app/billing-runs`. Switch to Customer in the preview
toolbar to inspect portal cards and invoice details; use its scenario selector
for loading/empty/error states. This mode uses isolated MSW handlers through an explicit API transport and never
updates a database or sends email. Normal dev defaults to mocks off; production
excludes the fixture modules. Prices and allowed actions come through the API
boundary even in preview. Sign-in and teammates' features remain their responsibility.

`/dev/styleguide` demonstrates shared components and is unavailable in production.
Private routes verify `/auth/me`; expired sessions clear identity and query caches.
API failures display readable errors and retries. Live backend integration, the
seeded golden flow, and browser screenshots remain pending; browser execution is
blocked in this restricted runtime. The frontend uses neutral shadcn tokens and
compact layouts; GSAP preserves cleanup and reduced-motion support.
