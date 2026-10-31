# Brightloop frontend (M4)

SvelteKit 3 + Svelte 5, **JavaScript**, Tailwind CSS 4, shadcn-svelte, and GSAP.
The backend API is owned by M1-M3 and uses **SQLite**. This frontend does not
connect to the database directly.

```sh
cd M4/frontend
npm ci
# Copy .env.example to .env and set VITE_API_URL to the team's API.
npm run dev
```

Node 22.12+ is required. All fonts/icons are bundled; installed builds run
without external asset services. Docker uses the same dev server on port 5173.
M1 can use `M4/frontend` as the compose web build context; compose is not edited here.

## Frontend preview

Run `npm run dev:preview` and open `http://127.0.0.1:5173/app/subscriptions`.
This development-only mode supplies sample records without a backend. The preview
toolbar switches admin/staff/customer roles and loading, empty, and error states.
Reset restores sample records. Actions, payments, PDFs, and billing runs are
simulated locally; no email is sent and no database is changed. Production builds
exclude the fixture modules, and `npm run dev` keeps mocks off by default.

| Page                                 | Route                                                |
| ------------------------------------ | ---------------------------------------------------- |
| Subscriptions / new / details / edit | `/app/subscriptions`, `/new`, `/:id`, `/:id/edit`    |
| Invoices / details                   | `/app/invoices`, `/app/invoices/:id`                 |
| Payments                             | `/app/payments`                                      |
| Billing runs                         | `/app/billing-runs`                                  |
| Customer subscriptions / details     | `/portal/subscriptions`, `/portal/subscriptions/:id` |
| Customer invoices / details          | `/portal/invoices`, `/portal/invoices/:id`           |

The dashboard at `/app/dashboard` includes report summary cards, a monthly revenue
graph, and overdue invoices. Date controls share a keyboard-accessible calendar
with month/year navigation and the same field validation as the forms.

Other members own authentication, catalog, rules, customer management,
profile, and payment history. Their current route components are placeholders.
Live API integration and the seeded golden-flow verification are deferred.

## Foundation hand-off

- `/` provides a simple workspace entry point with direct page links.
- `src/features/*/routes.js` is the one-time skeleton hand-off. Owners replace
  their placeholder components. Route manifests retain the canonical URL and roles,
  using Svelte components instead of React elements. SvelteKit owns routing.
- `src/lib/auth/session.js` exposes the `auth` store with `initialize`, `login`,
  `logout`, and `setSession`. Stored tokens are verified through `/auth/me`.
  Only the token is persisted. Private pages render in the browser; backend RBAC
  remains required. Query caches clear when the authenticated identity changes.
- `#lib/*` and `#src/*` are native package subpath imports. shadcn is configured
  for JavaScript (`typescript: false`) and the Nova style in `components.json`.
- The official registry Button was converted to JavaScript after the CLI's
  subprocess-based initialization was blocked by this Windows environment.
  It uses a 40px minimum target through the shared base styles.
- `src/api/client.js` supplies the generated OpenAPI client, bearer middleware,
  normalized errors, and expired-session handling. `src/api/schema.d.ts` is
  generated documentation for JavaScript, not handwritten TypeScript code.
- `npm run gen:api` fetches the live OpenAPI contract and updates the snapshot;
  it falls back to that snapshot when offline. The current snapshot contains only
  the provisional A4 auth contract. Regenerate when the backend G3 schemas arrive.
- Mocks default to **off**. Only `dev:preview` enables the isolated development
  worker. Feature components import API helpers, never sample business records.

## Checks

```sh
npm run check
npm run lint
npm test
npm run check:static
npm run build
# Install the browser once, then run responsive/browser checks:
npx playwright install chromium
npm run e2e
npm run shots
```

The browser suite covers 375/768/1280px, page errors, horizontal overflow,
anonymous redirects, and reduced motion. Screenshots go to ignored `test-results/`.
Native config loading avoids bundling native tool bindings on Windows.

## Integration gate

Shared components, admin/portal layouts, and M4's business screens are implemented.
The next stage validates them against the full backend contract. Business actions
come from server `allowed_actions`; prices and billing calculations remain on the
server. The preview's isolated response generator is not a production billing engine.

Work stays on `main` with conventional commits authored by the configured human
identity, following the user's latest instruction. Ask before a push unless that
push has already been authorized. Do not create new branches.

## Phase 1 checkpoint

Shared Nova primitives now include Badge, Card, Sheet, DropdownMenu, Separator,
and Skeleton. `PageHeader`, `MoneyCell`, and the INR/date formatters are available
for feature owners. `src/layouts/navConfig.js` owns all role-filtered navigation.
AdminLayout and PortalLayout mount under their guarded SvelteKit route trees,
with a mobile drawer, breadcrumbs, role chip, account menu, and logout.
The shared library now also includes DataTable, StatusBadge, loading/empty/error
states, validated forms and fields, asynchronous comboboxes, ConfirmDialog,
RoleGate, and mutation toasts. The development-only `/dev/styleguide` route is a
component workshop; it does not save business records. See
`../docs/modules/frontend.md` for the Svelte API and walkthrough.

DOM-level tests run with Svelte Testing Library and jsdom. They cover table
states and controls, accessible field errors, status rendering, and search timing.
Subscription, billing, and portal screens use these shared components.

SvelteKit's JavaScript checking uses TypeScript 6. The API generator's compiler
peer is overridden to that same version; API generation and checks validate the
combination. Application source remains JavaScript.
