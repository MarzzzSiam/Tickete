# Changelog

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
