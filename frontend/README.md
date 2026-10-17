# Frontend

Next.js App Router, React, TypeScript, Tailwind CSS and Radix primitives. Uses the original TICKETÉ logos and next/font for Playfair Display, Inter and JetBrains Mono.

## Run

Node 24 LTS is recommended. From `frontend/`:

```sh
npm ci
```

Copy `.env.example` to `.env.local` (PowerShell: `Copy-Item .env.example .env.local`). Then `npm run dev`. Open http://127.0.0.1:3000. Use the same 127.0.0.1 hostname for both apps to avoid cookie/origin mismatches in later phases.

Routes: `/` landing; `/events` empty listing; `/start` organizer account entry; `/design` component review; `/api/health` backend liveness check. Phase 1 adds `/signup`, `/login`, `/account`, `/forgot-password`, `/reset-password` and `/verify-email`. Account screens call Django using cookie authentication and CSRF. Email delivery, event creation, purchases, payment and QR delivery remain pending.

## Verify

```sh
npm run lint
npm run build
npm run typecheck
npm run format:check
npx playwright install chromium
npm run test:e2e
```

Browser tests start the local server automatically and check 1440 px desktop and 360 px mobile. They cover navigation, empty states, dialog focus restoration, quantity controls, select/checkbox/toast behavior, layout overflow and automated WCAG checks. Screenshots go to `../docs/screenshots`. Automated accessibility testing supplements manual visual/keyboard inspection.

The first build/dev run downloads fonts through next/font. Later builds bundle them locally. Network access is needed for initial dependency and font downloads. `npm run start` serves a completed production build.

Source logo padding is hidden using CSS viewport coordinates in `Brand`; originals remain unchanged. No QR/PDF artwork is generated in this phase. Internal preview metadata is noindex until release. Colors live in `src/styles/tokens.css`; components and the mobile drawer use Radix semantics.

Do not put service keys, database URLs or private email credentials in frontend variables. API_BASE_URL is server-only. NEXT_PUBLIC_API_BASE_URL contains only the browser-visible API address (default http://127.0.0.1:8000/api/v1). Both development servers must run for signup/login. See the root README for the manual test checklist. Production authentication/domain settings require deployment verification.

The real authentication browser test runs only with AUTH_E2E_LIVE=1 and an isolated database/Redis API, as configured in GitHub Actions. Do not enable it against the shared Supabase development database. Default local browser tests validate UI and mock service errors; they do not create accounts.
