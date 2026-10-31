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

Run `npm run dev`, then open `/dev/styleguide`. Try invalid fields, status chips,
the loading/error toggles, and a confirmation. The route is unavailable in
production and is not in product navigation. Sign-in and other teammates' feature
pages remain their responsibility. Private routes verify `/auth/me`; expired
sessions clear identity and cached queries. API failures display readable errors
and retries. Mocks are off; full API integration and the golden flow await the
backend gates. Browser screenshots remain unverified in the restricted runtime.
