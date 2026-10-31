# Brightloop design foundation

M4 owns the frontend in `M4/frontend`. Product code is SvelteKit + JavaScript,
Tailwind CSS, shadcn-svelte, and GSAP. The backend uses SQLite and remains with
its owners. React, React Router, and handwritten TypeScript are not used.
Generated OpenAPI declarations and TypeScript tooling support JavaScript checks.

| Token | Usage |
| --- | --- |
| `primary` / `primary-foreground` | Plum actions, brand, focus indicators |
| `background` / `foreground` | Warm neutral canvas and readable text |
| `card` / `border` | White surfaces and subtle boundaries |
| `secondary`, `muted`, `muted-foreground` | Quiet surfaces and supporting copy |
| `status-draft` | Neutral draft state |
| `status-active` | Green active/paid state |
| `status-warning` | Amber quotations, paused, outstanding |
| `status-danger` | Red overdue, errors, destructive actions |

Tokens live in `src/routes/layout.css`; components use semantic tokens and
built-in variants. Status colors support `/10` tints and always pair with text
and icons. Inter is bundled locally through Fontsource; Lucide icons are bundled.
There are no runtime font, image, or CDN requests.

Use an 8px layout grid, 40px minimum tap targets, and 16/24/32px application page
padding at phone/tablet/desktop widths. The planned sidebar is 240px with 24px
navigation group gaps; it becomes a drawer below 1024px. Verify 375/768/1280px.
The welcome page establishes the visual language. AdminLayout and PortalLayout
share role-filtered navigation, breadcrumbs, an account menu, and a mobile Sheet.

GSAP uses Svelte attachments, scoped targets, transform/opacity reveals, media
queries for reduced motion, and `revert()` on cleanup. Content stays visible
without animation. Keep motion short and functional.

Hard decisions: preserve the shared API contract while adapting React route
manifests to Svelte components; keep credentials browser-only and verify roles
through `/auth/me`; keep business prices, balances, and actions on the server.
Demo: open `/`, resize, enable reduced motion, then visit `/app/invoices` while
signed out to see the guard. If the backend is down, no fake identity or records
are substituted. G3 supplies the authoritative full OpenAPI snapshot.
