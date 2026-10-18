# Task breakdown

Status: implementation plan approved on 2026-10-07. As of 2026-10-18, authentication and event publishing are implemented and pass isolated CI; Supabase migrations are current. Live worker/email, hosted storage and final manual acceptance remain open. See the dated root README and `14-phase-1-event-publishing.md` for current evidence; earlier entries below preserve milestone history.

## Preparation

- [x] Read MD, fourteen-entity ERD, seven-page features PDF and nine-page PRD.
- [x] Draft architecture, data model, API outline, states, permission matrix and concurrency strategy.
- [x] Draft project rules, design system and phase acceptance criteria.
- [x] Confirm MD precedence and per-order plus per-email/event purchase cap with the user.
- [x] User approved the implementation plan before application development.

## Phase 0 — foundations (MVP)

Progress: repository, app scaffolds, locked dependencies, environment examples, Compose, Dockerfile, CI definition, initial user migration, health/OpenAPI, storage/gateway boundaries, brand tokens, core components, landing and preview routes are implemented. Local non-database tests/build/browser checks passed. Remaining: PostgreSQL/Redis provisioning and integration checks, Supabase connection later when configured, clean-machine/CI verification, and user visual review. Do not treat this as a completed production stack.

1. Set up monorepo tooling, ignore rules, CI and environment examples. Verify Python 3.12, Node and Docker availability; pin versions.
2. Scaffold Django apps and settings split (base/local/production), health API, error format and OpenAPI; initialize Next.js App Router/TypeScript/Tailwind.
3. Configure local PostgreSQL/Redis, Celery and adapter boundaries. Test Supabase connectivity when credentials are available; document pooler settings. No remote migrations before target verification.
4. Preserve source logos; prepare web assets without distorting/recoloring the artwork. Establish tokens and fonts, accessible Button first, then fields/cards/ticket card and remaining `/design` components.
5. Build branded landing shell with responsive navbar, hero, journey cards and footer. Avoid fabricated featured events or success statistics; label demo data explicitly.
6. Verify clean setup, backend health/database checks, frontend build/type/lint, basic browser interactions and desktop/360 px layouts. Capture screenshots, document limitations and request Phase 0 review.

Done when both apps run, README setup is tested, database connection status is explicit, CI passes and the user has reviewed the visual foundation. Supabase acceptance remains pending if credentials are absent.

## Phase 1 — event publishing (MVP)

2026-10-16: started at the user's request following reported worker deployment. First increment implements cookie JWT authentication and CSRF bootstrap/enforcement with twelve passing security tests. Signup/login, recovery and business APIs remain pending. See `13-phase-1-authentication.md`. Phase 0 live worker/Redis acceptance is still open and tracked separately.

2026-10-18: implemented registration, session login/refresh/logout, profile, password change and verification/reset APIs. All 51 backend tests passed in isolated PostgreSQL CI, including concurrent refresh; frontend CI also passed. Applied the session/challenge migration to Supabase with none pending. Frontend forms, provider delivery, event APIs and the earlier live worker acceptance remain pending.

2026-10-18 frontend follow-up: connected signup/login/account/profile/password/logout and verification/reset link forms. CI run 39064180434 passed 13 browser tests, including real Django/PostgreSQL/Redis signup/login/refresh/profile/logout flows on desktop and mobile. Shared Supabase was not used for automated account creation. Hosted PostgreSQL and Redis readiness passed after increasing the configurable cache/readiness timeout from three to five seconds. Manual account testing is documented in the root README; transactional email and worker acceptance remain pending.

1. Implement User and authentication backend first: registration, verification, login/refresh/logout cookies, reset, profile, CSRF, throttles and permission tests. Connect forms after API contracts stabilize.
2. Implement event/category/custom-field models and migrations, validation, draft edits/preview and submission. Build the four-step creation UI against those endpoints.
3. Implement admin queue, approve/reject transitions, unique public slug, notifications and proposed MVP audit record creation. Connect review drawer and notification UI.
4. Implement public approved-event APIs, SSR event page, listing/search and metadata. Ensure drafts/rejections are inaccessible by public URLs.
5. Seed fictional admin, organizer and approved event with three categories. Add sample paid orders/tickets only once Phase 2 models exist.
6. Verify create -> submit -> approve/reject -> public link, duplicate transitions, unverified submission denial, cross-event access, SSR share metadata and mobile forms. Document screenshots and request review.

2026-10-18 event-publishing follow-up: implemented items 2–4 and automated create/submit/approve/public-page coverage. CI passed 70 backend tests and 16 browser tests. Applied event, notification, audit and privacy migrations to Supabase; verified no pending migrations and RLS/browser-role restrictions on 17 tables. Brevo account-email adapter is prepared, with private setup in `15-transactional-email.md`. Live delivery, hosted storage, manual review, expanded listing filters and the full three-category demo event remain outstanding; this does not mark the entire phase complete.

## Phase 2 — purchasing and delivery (MVP)

Resolve free tickets and name requiredness first. Implement confirmed per-order and per-email/event caps, holds/order snapshots/idempotency and PostgreSQL races; dummy gateway/OTP and failure recovery; ticket issuance; approved HTML mock-up then PDF/QR; Celery delivery and reconciliation; confirmation/gifting/download; recovery by email OTP in Phase 2. Test guest and registered journeys, same-email races across categories, last-seat contention, retries, expiry races, private access, and multi-page PDF scanability. Review before Phase 3.

## Phase 3 — venue operations (MVP)

Invitations and verified acceptance, member roles/revocation, camera and manual scanning, atomic single-use admission, cancellation, all scan outcomes and live count. Test simultaneous scans, wrong event, role boundaries and revocation. Check 360 px device usability and camera permissions over HTTPS. Review before Phase 4.

## Phase 4 — reporting and launch (MVP)

Dashboard charts, final report/close, cancelled/unlimited category behavior, performance/load and security checks, observability, deployment manifests, backups/restore drill and staging end-to-end acceptance. Confirm hosting, sender domain and Supabase credentials. Production launch requires verified integrations and user release decision.

## Phase 5 — V2, separate approval

Google login, CSV/export PDF, offline attendee list, approved-event change rules/holder notices, registered order history, activity/audit views, suspension. Later: promo codes, waitlist, duplicate events, real provider. Refunds/payouts/fees/native apps/seat maps remain outside scope.
