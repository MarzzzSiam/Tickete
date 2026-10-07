# Frontend

Next.js App Router, React, TypeScript, Tailwind CSS and Radix primitives. Uses the original TICKETÉ logos and next/font for Playfair Display, Inter and JetBrains Mono.

## Run

Node 24 LTS is recommended. From `frontend/`:

```sh
npm ci
```

Copy `.env.example` to `.env.local` (PowerShell: `Copy-Item .env.example .env.local`). Then `npm run dev`. Open http://127.0.0.1:3000. Use the same 127.0.0.1 hostname for both apps to avoid cookie/origin mismatches in later phases.

Routes: `/` landing; `/events` honest empty listing; `/start` organizer availability notice; `/design` interactive component review; `/api/health` server-to-server backend liveness check. These are Phase 0 previews. No event creation, authentication, purchases, payment, QR or delivery are claimed functional yet.

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

Do not put service keys, database URLs or private email credentials in frontend variables. API_BASE_URL is server-only. Production authentication/domain settings will be verified during Phase 1 and deployment planning.
