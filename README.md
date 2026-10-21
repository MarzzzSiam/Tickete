# TICKETÉ

Event ticketing for Bangladesh. One monorepo with a Django REST Framework backend and a Next.js frontend. Currency: BDT. Timestamps: UTC in storage, Asia/Dhaka in the interface.

## Current status

2026-10-21 — Phase 3 venue operations implemented after owner-confirmed ticket email delivery: organizer purchase visibility, accepted email invitations, event roles, camera/manual check-in and atomic duplicate-entry rejection. Supabase migrations are applied with none pending; all three new tables have RLS and deny browser-role reads. The existing free local processor also handles invitations. [Final CI](https://github.com/MarzzzSiam/TICKETE/actions/runs/39603995434) passed 116 backend and 24 browser tests, production build, lint, types and schema checks. Desktop/mobile screenshots were reviewed. See [venue operations](docs/17-phase-3-venue-operations.md) for acceptance steps and remaining work.

2026-10-21 — checkout account isolation: saved checkout restoration now waits for identity verification and checks both the account and browser session generation. Login/logout clears checkout access across tabs; legacy unscoped entries are discarded. Guest reload restoration is retained within the same guest session. An unavailable account service blocks restoration rather than treating the visitor as a guest. Verified by [CI run 39565770545](https://github.com/MarzzzSiam/TICKETE/actions/runs/39565770545): 22 browser tests and the backend suite passed; local production build, type checking and lint passed.

2026-10-21 — local delivery troubleshooting: a paid order remained queued with zero attempts because `process_ticket_jobs` was not running. Django's web server does not consume this queue; keep the processor terminal open alongside Django and Next.js. Corrected explicit banner sizing to avoid the unrelated Next.js image aspect-ratio warning. No ticket email was sent during this diagnostic check.

2026-10-21 — verification: [CI](https://github.com/MarzzzSiam/TICKETE/actions/runs/39556864201) passed **100 backend tests and 20 browser tests**. Checkout/delivery migrations are applied to Supabase with none pending. The approved two-page PDF was rendered, visually reviewed, and both QR codes decoded. Real ticket-mailbox acceptance is still to be tested with the local processor running.

2026-10-21 — Phase 2 checkout and approved PDF delivery implemented: paid-category selection, guest/account details, gifting, optional names, ten-minute inventory holds, per-order/per-email caps and idempotent simulated payment. The owner approved `/ticket-preview`; PDFs now include unique QR codes, private downloads and queued email/gift receipts. A free local processor replaces the need for a paid worker during development. Verification and migration status are tracked in [Phase 2 checkout](docs/16-phase-2-checkout.md). Recovery/resend and launch acceptance remain pending. The owner also confirmed event creation/viewing and real Gmail SMTP delivery.

2026-10-20 — budget update: the owner requires zero-cost development. Do not provision paid services. Local account email processing is available with `LOCAL_ACCOUNT_EMAIL_SYNC=True` in `backend/.env`; restart Django after changing it. No hosted worker is needed for these local verification/reset requests. Gmail SMTP remains unverified: encrypted connections succeeded but disconnected during authentication on both ports 587 and 465. To continue development without inbox delivery, set `EMAIL_PROVIDER=console` locally and use the private link printed in the Django terminal. Hosted launch and background job infrastructure remain unresolved; no promise of unlimited free hosting is made.

2026-10-18: Phase 1 authentication and event publishing are implemented, including the organizer studio, admin review, notifications and approved public event pages. [CI run 39116501044](https://github.com/MarzzzSiam/TICKETE/actions/runs/39116501044) passed 70 backend tests (91% coverage) and 16 browser tests, including the real create/submit/approve/public-page flow. All event and privacy migrations are applied to Supabase, with none pending; row security and denied browser-role table privileges were verified on 17 Django tables. The Brevo email adapter is prepared, but hosted email/worker delivery and remaining Phase 1 acceptance are not complete. Follow [development without Docker](docs/12-cloud-development.md), [event publishing](docs/14-phase-1-event-publishing.md), and [private email setup](docs/15-transactional-email.md).

Start with the [Phase 0 review](docs/11-phase-0-review.md), [system design](docs/05-system-design.md), and [task breakdown](docs/07-task-breakdown.md). The user confirmed ticket caps per order AND per buyer email across an event; see [decisions](docs/decisions/0001-source-reconciliation.md).

## Dated phase progress

### 2026-10-20 — Gmail SMTP setup

At the owner's request, added Django Gmail SMTP support for `hello.tickete@gmail.com`, superseding the original email-provider choice. Local and hosted worker settings support encrypted SMTP with private app-password credentials, sanitized delivery failures and existing Celery retries. Added a direct test-email command and [Gmail setup instructions](docs/15-transactional-email.md). Eight focused mocked email tests, Ruff, Black and Django system checks passed. Live SMTP/inbox and worker acceptance remain pending private credential setup; Phase 2 checkout has not started.

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

### 2026-10-18 — Phase 1 event publishing and email adapter

Implemented organizer draft/category/custom-field APIs, verified submission, admin approval/rejection, audit records, in-app notifications, banner validation and approved-only public content. Added the four-step organizer studio, review drawer, notifications screen and server-rendered public event page/share metadata. CI passed 70 backend and 16 browser tests (two intentional browser skips); lint, formatting, types, production build and schema checks passed. Applied four event/notification/audit/privacy migrations to Supabase and verified none pending. Confirmed RLS and denied anon/authenticated table privileges on all 17 Django tables. The Brevo HTTPS account-email adapter is prepared but live sending remains unconfigured. See [event publishing](docs/14-phase-1-event-publishing.md) and [private email setup](docs/15-transactional-email.md). This is not a Phase 2/payment release.

## Structure

- `backend/`: Python 3.12, Django, DRF, PostgreSQL, Celery.
- `frontend/`: Next.js App Router, TypeScript, Tailwind.
- `docs/`: requirements, design, verification, deployment and decisions.
- `docs/source/`: unchanged copies of the supplied requirements and ERD.

## Run locally

Prerequisites: Python 3.12 and Node 24. Follow the [cloud development guide](docs/12-cloud-development.md) for hosted PostgreSQL and Redis without local Docker, then the [backend guide](backend/README.md) and [frontend guide](frontend/README.md). Alternatively, local PostgreSQL 17 and Redis 7 can be started with `docker compose up -d`. Full clean-machine setup awaits verification with working services.

Frontend: `cd frontend`, `npm ci`, `npm run dev`. Open [local preview](http://127.0.0.1:3000) and [design system](http://127.0.0.1:3000/design). Backend process health: `http://127.0.0.1:8000/api/v1/health/`; frontend-to-backend check: `http://127.0.0.1:3000/api/health`.

Signup, login, account screens and event publishing now connect to Django. Open `/organizer/events` to create drafts; verified email is required to submit. Admins review at `/admin/events`, and approved events appear at `/events`. Purchase inventory, dummy checkout and ticket issuance remain pending. No real payments are accepted.

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
## 2026-10-21 — Phase 2 ticket PDF and delivery

The ticket design is approved. Checkout now queues one PDF per order (one page per ticket), private downloads, ticket email and gift receipts. Run the free local processor in a separate backend terminal: `.\.venv\Scripts\python.exe manage.py process_ticket_jobs`. Keep it running while testing purchases. See [Phase 2 setup and status](docs/16-phase-2-checkout.md). Payment remains simulated; recovery/resend and scheduled expiry cleanup are still pending.
