# TICKETÉ

Event ticketing for Bangladesh. One monorepo with a Django REST Framework backend and a Next.js frontend. Currency: BDT. Timestamps: UTC in storage, Asia/Dhaka in the interface.

## Current status

2026-10-18: Phase 1 authentication endpoints are implemented: registration, cookie login, refresh rotation, logout, profile, password change and verification/reset requests and confirmations. Database-backed sessions provide revocation; email links are expiring and single-use. All 51 backend tests passed in isolated PostgreSQL CI, alongside frontend checks. The additive authentication migration is applied to Supabase, with none pending. Frontend account forms are implemented: CI passed 13 browser tests, including real API signup/login/session refresh/profile/logout on desktop and mobile. Hosted email delivery and event publishing are not complete. The previously reported worker deployment still needs live acceptance. Follow [development without Docker](docs/12-cloud-development.md) and the [Phase 1 authentication contract](docs/13-phase-1-authentication.md).

Start with the [Phase 0 review](docs/11-phase-0-review.md), [system design](docs/05-system-design.md), and [task breakdown](docs/07-task-breakdown.md). The user confirmed ticket caps per order AND per buyer email across an event; see [decisions](docs/decisions/0001-source-reconciliation.md).

## Dated phase progress

Keep this history when updating the current status. Append a dated entry for each milestone or change of direction; distinguish implemented work from verified integrations.

| Date | Phase | Work and verification | Remaining work |
|---|---|---|---|
| 2026-10-07 | Preparation | Requirements reviewed; architecture and implementation plan approved. MD takes precedence; caps apply per order and per email/event. | Begin foundation. |
| 2026-10-07 | Phase 0 — foundation | Django/Next.js scaffold, branding, preview screens, CI definition and initial user migration implemented. Local UI/build and non-database checks passed. | Live database, Redis, worker and CI verification. |
| 2026-10-14 | Phase 0 — cloud database | Switched from local Docker to hosted services. Supabase connection verified; 19 migrations applied, none pending. Credentials excluded from Git. | Redis, worker and isolated database tests. |
| 2026-10-14 | Phase 0 — GitHub | Foundation PR #1 merged into main; merge confirmed from the remote repository. | Independently inspect CI results. |
| 2026-10-14 | Phase 0 — background jobs, in progress | Prepared hosted worker settings, task-result verification command and Render setup instructions. | Create Render services, configure credentials and verify a real job. No worker deployed yet. |
| 2026-10-16 | Phase 0 — Redis and worker deployment | Hosted Redis PING succeeded after IP allow-list troubleshooting. Worker settings passed Django checks. A live task/result check failed; worker execution is not yet verified. | Deploy the Render background worker, then repeat the end-to-end task check. |
| 2026-10-16 | Phase 1 — authentication started | User requested progression after reporting worker deployment. Implemented cookie JWT authentication, CSRF bootstrap and unsafe-request CSRF checks. Twelve security tests pass; OpenAPI updated. | Registration, login/refresh/logout, verification/reset, profile and event publishing. Redis connectivity regressed; deployed worker execution remains unverified. |

Phase 1 is proceeding at the user's request while outstanding foundation integration checks remain tracked. Phases 2–4 cover purchases/delivery, venue operations, then reporting and launch; see the task breakdown for acceptance criteria.

### 2026-10-18 — Phase 1 authentication API increment

Implemented the authentication endpoints, session/refresh revocation and hashed verification/reset challenges. PostgreSQL integration tests cover session replay, logout, password reset, CSRF, profile permissions, throttling and simultaneous refresh. [CI run 39061450192](https://github.com/MarzzzSiam/TICKETE/actions/runs/39061450192) passed 51 backend tests (90% overall backend coverage) plus frontend lint/format/build/type/browser checks. The additive session/challenge migration was then applied to Supabase, with none pending. Email requests enqueue work and do not claim delivery; frontend link handlers and hosted email integration remain pending. Manual CI dispatch is available when pushes do not trigger a run.

## Structure

- `backend/`: Python 3.12, Django, DRF, PostgreSQL, Celery.
- `frontend/`: Next.js App Router, TypeScript, Tailwind.
- `docs/`: requirements, design, verification, deployment and decisions.
- `docs/source/`: unchanged copies of the supplied requirements and ERD.

## Run locally

Prerequisites: Python 3.12 and Node 24. Follow the [cloud development guide](docs/12-cloud-development.md) for hosted PostgreSQL and Redis without local Docker, then the [backend guide](backend/README.md) and [frontend guide](frontend/README.md). Alternatively, local PostgreSQL 17 and Redis 7 can be started with `docker compose up -d`. Full clean-machine setup awaits verification with working services.

Frontend: `cd frontend`, `npm ci`, `npm run dev`. Open [local preview](http://127.0.0.1:3000) and [design system](http://127.0.0.1:3000/design). Backend process health: `http://127.0.0.1:8000/api/v1/health/`; frontend-to-backend check: `http://127.0.0.1:3000/api/health`.

Signup, login and account screens now connect to Django. Event creation, real inventory, dummy checkout and ticket issuance remain pending. No real payments are accepted.

### 2026-10-18 — Phase 1 frontend authentication increment

Added signup/login, account editing, password changes, logout and verification/reset link screens. Browser requests use HttpOnly session cookies, fresh CSRF tokens and serialized refresh across tabs where Web Locks are supported. Forms validate input and display API errors. Email delivery remains pending; a request confirmation does not prove delivery. Automated browser coverage includes an opt-in real API flow using disposable CI PostgreSQL and Redis, never shared Supabase. [CI run 39064180434](https://github.com/MarzzzSiam/TICKETE/actions/runs/39064180434) passed all backend checks and 13 browser tests (one desktop-only menu skip), including real API flows on desktop and mobile. Local lint, formatting, type checking, production build and 11 UI browser tests also passed. A subsequent hosted readiness check exposed the three-second Redis timeout; making the cache/readiness timeout configurable with a five-second default restored both PostgreSQL and Redis readiness. Two focused readiness tests and lint passed for that adjustment. Restart the backend to load it. Hosted worker/email acceptance remains outstanding.

### Manual authentication check in VS Code

Open `D:\TICKETÉ` and keep two PowerShell terminals running:

```powershell
cd 'D:\TICKETÉ\backend'
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

```powershell
cd 'D:\TICKETÉ\frontend'
npm.cmd run dev
```

Keep the saved backend `.env`. The frontend API defaults to `http://127.0.0.1:8000/api/v1`; set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` only if changing it, then restart Next.js. Backend `FRONTEND_ORIGIN` must match `http://127.0.0.1:3000`. Do not mix `localhost` and `127.0.0.1`.

1. Open [signup](http://127.0.0.1:3000/signup), create a test attendee or organizer account, then follow **Go to log in**.
2. Log in and check your name, email and role on the account page.
3. Save a changed name, reload, and confirm it persists. Try a second tab after the five-minute access expiry to check session refresh.
4. Log out, then revisit `/account`; private details should be hidden. Try an incorrect password and confirm it does not sign you in.
5. Optionally change your password from the account page, then log in with the new password.

Signup/login require working PostgreSQL **and Redis**. A service-unavailable message requires checking backend logs and Redis connectivity, not bypassing throttles. Verification/reset emails still require the email provider and updated worker deployment before manual inbox testing. Never commit `.env` files or paste credentials into issue reports.

CI runs lint, type checks, production build, browser accessibility tests and PostgreSQL-backed tests. The repository is connected to `MarzzzSiam/TICKETE`; the first manually dispatched passing run is recorded above. Pre-commit hooks are provided; activate the backend venv before `pre-commit install` and before committing.
