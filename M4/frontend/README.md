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

## Phase 0 hand-off

- `/` is the initial visual foundation. Business/auth pages are explicit placeholders.
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
- Mocks default to **off**. MSW is installed but no mock business handlers or
  startup wiring are supplied before G3. No business data is hardcoded in the UI.

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

## Next gate

Phase 1 supplies shared components and admin/portal layouts. G3 supplies the full
backend contract. Phase 2 adds subscription, invoice/payment, billing-run, and
portal screens. Business actions come from server `allowed_actions`; prices and
billing calculations remain on the server.

Work stays on a feature branch with conventional commits authored by the configured
human identity. Ask the user before every push; never push to main directly.
