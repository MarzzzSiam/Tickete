# Changelog

## 2026-10-21 — Phase 2 checkout and ticket design preview

- Recorded owner-confirmed event and Gmail delivery acceptance, zero-cost constraint, excluded free tickets and optional attendee names.
- Added reserved orders, category holds, simulated payment attempts, ticket issuance, capability authorization, idempotency and PostgreSQL race tests.
- Connected four-step responsive checkout and truthful confirmation states; prepared a branded HTML ticket mock-up for approval before PDF implementation.

## 2026-10-20 — Gmail SMTP support

- Recorded the zero-cost constraint and deferred paid worker provisioning. Added opt-in local synchronous account-email processing, guarded by DEBUG, and a console-mail fallback guide. Hosted processing remains queued.
- Distinguished SMTP authentication rejection from unexpected disconnection without exposing provider responses or credentials.

- Owner selected Gmail SMTP instead of the previously planned Brevo setup.
- Added encrypted Django SMTP delivery, hosted worker support, safe errors and focused mocked tests.
- Added explicit-recipient test-email command and private app-password instructions. No real email sent or credentials configured by this change.

## 2026-10-18 — event publishing and transactional email preparation

- Added events, categories, custom fields, in-app notifications and admin audit models with additive migrations; owner/admin permissions, schedule checks and locked review transitions.
- Added organizer draft editor, review drawer, approved public event listing/detail with server rendering and share metadata, and notification inbox.
- Added validated/re-encoded banner storage and approved-only public banner reads.
- Prepared a Brevo HTTPS adapter and private configuration guide; no provider credentials or real email delivery are claimed configured. Personal mailbox passwords are not used.
- Verified 70 backend tests (91% coverage) and 16 browser tests in CI run 39116501044, including the real event publishing flow; all lint/build/schema/type checks passed.
- Applied four migrations to Supabase with none pending; verified RLS and denied anon/authenticated table privileges on 17 Django tables. Updated dated README progress and saved editor/public-page screenshots.

## 2026-10-18 — authentication endpoints

- Added registration, login, rotating refresh, logout, profile and password-change APIs; protected unsafe requests with CSRF and Redis-backed IP/email throttles that fail closed on cache failure.
- Added database-backed session revocation and hashed, single-use verification/reset challenges with an additive migration. Password change/reset revoke sessions.
- Added generic password-reset dispatch and a Celery mail task; hosted mail provider and frontend link handlers remain unconfigured.
- Verified 51 backend tests on isolated PostgreSQL, including concurrent refresh; frontend CI also passed. Overall backend coverage is 90%. Applied the additive authentication migration to the Supabase development project and verified none pending.
- Added manual CI dispatch after automatic pushes produced no runs. Bounded Redis connection/read timeouts for account throttling and task dispatch; hosted worker/mail acceptance remains separate.

## 2026-10-16 — Phase 1 authentication started

- User requested the next phase after reporting Render worker deployment; infrastructure acceptance remains open because live worker and subsequent Redis checks failed.
- Implemented cookie JWT authentication and explicit Django CSRF enforcement, plus an anonymous, non-cacheable CSRF bootstrap endpoint.
- Added twelve passing security tests and regenerated OpenAPI. Signup/login, verification/reset and event publishing remain pending.
- Preserved dated phase milestones in the README and added the authentication implementation contract.

## 2026-10-07 — Phase 0 implementation

- User approved the design and implementation plan; Supabase deferred in favor of local setup.
- Added Django settings, UUID email identity/migration, health and OpenAPI, structured logging/error contracts, Celery configuration, private storage adapters and payment gateway protocol.
- Added Next.js/TypeScript/Tailwind, original brand assets, accessible Radix controls, landing page, event/organizer empty states and interactive design preview.
- Added environment examples, pinned dependencies, Compose PostgreSQL/Redis services, backend Dockerfile, CI workflow and pre-commit configuration.
- Production frontend build, lint/type/format checks, eleven non-database backend tests, and five browser checks passed (one desktop-only skip of a mobile-menu test). Automated WCAG checks passed for the landing/design pages. Fixed mobile decoration overflow discovered in visual review.
- PostgreSQL/Redis readiness failed honestly because services are absent. Database migrations/tests, worker dispatch, hosted storage/email, CI and Docker build remain unverified. Development-only lint dependency advisories are documented in the review.

## 2026-10-07 — planning baseline

- Reviewed build prompt, PRD, features/core flow, fourteen-entity ERD and supplied logos.
- Created requirements summary, user journeys, proposed system design, project rules, phase breakdown and brand specification.
- Recorded source conflicts, operational risks and product questions explicitly.
- User confirmed limits per order AND per email/event; MD is the latest authority for other document differences. Updated the serialized inventory and cap design accordingly.
- No application code, tests, migrations, provider connection, deployment or production claims in this baseline.
# 2026-10-21 — approved ticket PDF implementation

- Added one-page-per-ticket PDF generation, embedded brand fonts and private QR images.
- Added a durable local delivery processor, retry tracking, gift receipts and capability-protected downloads.
- Kept zero-cost local execution; no paid Render worker is needed. Recovery/resend remains pending.
