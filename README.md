# TICKETÉ

**Event discovery, ticketing and one-time venue admission for Bangladesh.**

TICKETÉ connects organizers, attendees and venue teams. Organizers prepare events for administrative review, sell tickets with optional coupons, manage volunteers and monitor attendance. Buyers receive branded PDF tickets, while authorized staff admit each valid ticket only once using a QR code or printed ID.

This repository contains the complete **Next.js frontend and Django REST backend**. Currency is **BDT**; timestamps are stored in UTC and displayed in **Asia/Dhaka**. Payments are **simulated bKash/Nagad transactions**, not real payments.

## Project links

- [Live application](https://tickete-ten.vercel.app)
- [Explore events](https://tickete-ten.vercel.app/events)
- [Login](https://tickete-ten.vercel.app/login) · [Register](https://tickete-ten.vercel.app/signup)
- [Organizer studio](https://tickete-ten.vercel.app/organizer/events)
- [Find my ticket](https://tickete-ten.vercel.app/find-my-ticket)
- [Backend health](https://tickete-api.onrender.com/api/v1/health/)
- [GitHub repository](https://github.com/MarzzzSiam/TICKETE) · [Automated checks](https://github.com/MarzzzSiam/TICKETE/actions)

The free backend can sleep when idle. Open the site before demonstrating it; the first request may take about a minute or longer. A health response establishes process availability, not database readiness or successful email delivery.

## Main features

- **Accounts:** registration, email verification, login/logout, profile editing and password recovery.
- **Event publishing:** four-stage editor, banners, schedules, venues, ticket categories, custom questions, administrator review and notifications.
- **Inventory:** timed reservations, category capacity and purchase caps per order and per buyer email across an event.
- **Coupons:** up to three codes per event, discounts from 1–100%, and owner-controlled pause/resume. A valid 100% coupon confirms a zero-total order without payment.
- **Checkout:** guest/account purchases, gifting, optional attendee names and simulated payment.
- **Digital tickets:** branded PDFs, one page per ticket, unique QR credentials, readable IDs, private downloads and queued email delivery.
- **Recovery:** email-code verification and resend to the original recipient.
- **Venue operations:** accepted team invitations, scoped roles, camera/manual check-in and duplicate-entry rejection.
- **Reporting:** sales/category/attendance summaries and permanent event closure with a fixed final report.
- **Responsive UI:** visible form controls, keyboard focus, subtle motion and pause/reduced-motion support.

## Roles and access

All registered roles use the same login page. Team permissions apply to a specific event.

| Role | Responsibilities |
| --- | --- |
| Buyer / guest | Browse, purchase, receive tickets and recover eligible orders. |
| Organizer / owner | Create and submit events; manage coupons, purchases, teams and closure. |
| Manager | Permitted event editing, purchase visibility, reports and check-in. |
| Scanner | Admission tools and limited attendance information; no general buyer-email list. |
| Viewer | Read permitted summaries/reports; cannot check in attendees. |
| Administrator | Publication review and administrative purchase/report views; no automatic owner or scanner permissions. |

There is no universal administrator password. Create an administrator in your environment using the command below. Share evaluator credentials privately, never in this README.

## Technology stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | Next.js, React, TypeScript | Public pages and role-based workspaces |
| UI / forms | Tailwind CSS, Radix, Lucide, React Hook Form, Zod | Styling, controls, icons and validation |
| Backend | Python 3.12, Django, Django REST Framework, Gunicorn | API, transactions and application server |
| Authentication | Simple JWT, Django password hashing, explicit CSRF protection | Cookie sessions and protected requests |
| Database | PostgreSQL, Psycopg, Supabase Session pooler | Relational state and inventory authority |
| Jobs / cache | Celery, Redis-compatible Valkey, Django job processor | Account email and durable ticket work |
| Tickets / storage | WeasyPrint, qrcode, qr-scanner, Supabase Storage | PDF generation, scanning and private files |
| Email | Gmail SMTP locally; Brevo HTTPS in deployment | Verification, recovery, invitations and tickets |
| Quality | pytest, Playwright, axe, Ruff, Black, ESLint, Prettier | Behavioral, accessibility and code checks |
| Hosting / CI | Vercel, Render, Supabase, GitHub Actions | Deployment and automated validation |

Exact versions are defined in [frontend/package.json](frontend/package.json), its lockfile and [backend/requirements/](backend/requirements/). Install those dependencies rather than upgrading during initial setup.

## System overview

```mermaid
flowchart TD
    Browser[Buyer / organizer / event team] --> Frontend[Next.js - Vercel]
    Frontend --> API[Django REST API - Render]
    API --> DB[(PostgreSQL - Supabase)]
    API --> Redis[(Redis / Valkey)]
    Redis --> AccountWorker[Celery account-email worker]
    DB --> TicketWorker[Durable ticket job processor]
    API --> Storage[Private Supabase Storage]
    TicketWorker --> DB
    TicketWorker --> Storage
    TicketWorker --> Brevo[Brevo HTTPS email]
    AccountWorker --> Brevo
```

PostgreSQL is the authority for stock, orders and admission. Redis is not the inventory store. Account-email tasks use Celery/Redis; ticket jobs persist in PostgreSQL. In the free deployment, the API and processors share one Render web instance.

## Repository structure

| Path | Contents |
| --- | --- |
| `frontend/src/app/` | Next.js routes and layouts |
| `frontend/src/components/` | Shared UI, checkout and organizer components |
| `frontend/src/lib/`, `frontend/src/styles/` | Utilities and styling |
| `frontend/public/brand/` | TICKETÉ logo assets |
| `backend/apps/` | Accounts, events, orders, payments, tickets, teams and venue operations |
| `backend/config/` | Django settings and application configuration |
| `backend/requirements/`, `backend/tests/` | Python dependencies and tests |
| `docs/` | Requirements, design, API schema and feature/deployment notes |
| `.github/workflows/ci.yml` | Isolated backend and frontend checks |
| `docker-compose.yml` | Optional local PostgreSQL/Redis services |
| `render.yaml`, `backend/Dockerfile` | Hosted backend configuration |

## Run locally

### 1. Prerequisites

- Git and VS Code or another editor.
- **Python 3.12** and **Node.js 24** with npm.
- PostgreSQL and Redis: your own hosted development services or local services.
- Native WeasyPrint libraries for PDFs. Follow the [installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation); Python packages alone do not supply every native library.

The existing Windows workstation uses a portable PDF runtime in `.tools/pdf-runtime/ucrt64/bin`; ignored binaries are not included in a fresh clone. Linux dependencies are defined in the backend Dockerfile. Prefer separate development database/storage resources.

These commands use **Windows PowerShell**. `npm.cmd` avoids PowerShell script-policy issues. On macOS/Linux use `npm`, `python3.12` and the virtual environment's `bin/python` instead.

### 2. Clone and install

```powershell
git clone https://github.com/MarzzzSiam/TICKETE.git
cd TICKETE
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/local.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd ..\frontend
npm.cmd ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
```

If the folder already exists, open it and skip cloning. Do not overwrite a working `.env`.

### 3. Configure backend services

Edit `backend/.env` privately. For hosted development services:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=YOUR_PRIVATE_DEVELOPMENT_SECRET
DATABASE_URL=postgresql://USER:ENCODED_PASSWORD@SESSION_POOLER_HOST:5432/postgres?sslmode=require
DB_CONN_MAX_AGE=0
REDIS_URL=rediss://USER:PASSWORD@REDIS_HOST:6379?ssl_cert_reqs=required
ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_ORIGIN=http://127.0.0.1:3000
STORAGE_BACKEND=local
EMAIL_PROVIDER=console
LOCAL_ACCOUNT_EMAIL_SYNC=True
TRUST_PROXY_SSL_HEADER=False
```

These placeholders are not usable credentials. Use the complete Supabase Session pooler URI and percent-encode special characters in its password component. For external hosted Redis, allow your current **public IPv4 address** with `/32`, not your private LAN address. See [development without Docker](docs/12-cloud-development.md).

Alternatively, run `docker compose up -d` from the repository root and use the matching local URLs from `backend/.env.example`. Compose supplies the local database/Redis; start application processes separately below.

### 4. Configure the frontend

Use these values in `frontend/.env.local`:

```dotenv
API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
SITE_URL=http://127.0.0.1:3000
```

Leave production `BACKEND_ORIGIN` unset locally. Use `127.0.0.1` consistently instead of alternating with `localhost`.

### 5. Prepare the database and administrator

From `backend`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py check_services
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Confirm the target database before applying migrations. Run `createsuperuser` only when an administrator is needed; enter a private email/password at its prompts. Sign in through the frontend and open `/admin/events`. Complete email verification if an action requires it.

### 6. Start three terminals

Run each block in a separate terminal, starting from the repository root.

**Terminal 1 — Django API**

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

**Terminal 2 — Next.js frontend**

```powershell
cd frontend
npm.cmd run dev
```

**Terminal 3 — Ticket and delivery jobs**

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py process_ticket_jobs
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). Keep the processor running for queued PDFs, ticket messages, invitations and recovery work. `LOCAL_ACCOUNT_EMAIL_SYNC=True` supports local account verification/reset without a separate Celery process. Stop each terminal with `Ctrl+C`.

Local diagnostics: [API health](http://127.0.0.1:8000/api/v1/health/), [frontend API health](http://127.0.0.1:3000/api/health) and [API documentation](http://127.0.0.1:8000/api/v1/docs/).

## Email configuration

**Console mode:** `EMAIL_PROVIDER=console` prints messages and verification links in the terminal; it sends nothing to an inbox.

**Local Gmail SMTP:** use a Gmail app password, not the normal account password:

```dotenv
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=YOUR_SENDER@gmail.com
EMAIL_HOST_PASSWORD=YOUR_PRIVATE_APP_PASSWORD
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=TICKETÉ <YOUR_SENDER@gmail.com>
SUPPORT_EMAIL=YOUR_SENDER@gmail.com
```

**Hosted email:** use `EMAIL_PROVIDER=brevo`, a private `BREVO_API_KEY` and a verified sender. Render free hosting blocks common SMTP ports, so hosted mail uses Brevo HTTPS while Gmail remains a local option. See [email setup](docs/15-transactional-email.md) and [deployment](docs/21-free-submission-deployment.md).

Restart after changing configuration. To send a test to an inbox you control, run from `backend`:

```powershell
.\.venv\Scripts\python.exe manage.py test_email --to YOUR_OWN_EMAIL
```

## Application workflows

### Organizer and administrator

1. Register as an organizer, verify email and open **Organizer studio**.
2. Create an event through **Details → Tickets → Form fields → Review**. Set venue, schedules, categories, prices, capacity, purchase limits and questions. Add a banner through the saved workspace.
3. Optionally enable up to three coupons. Codes are case-insensitive and discounts are whole numbers from 1–100%.
4. Submit the event. An administrator approves or rejects it at `/admin/events`.
5. Manage purchases, coupons and team invitations from the saved event. Coupon codes/percentages are immutable after creation; pause/resume controls availability.
6. Review reports and permanently close the event only after admission finishes. Closure stops sales/check-in and freezes the final report.

### Buyer and recipient

1. Select an event and quantities, then enter details as a guest or signed-in user.
2. Optionally enter a gift recipient, attendee names and coupon; answer required custom questions.
3. Reserve tickets. Holds last up to ten minutes, shortened by applicable deadlines. Paid tickets plus active holds count toward the buyer-email event limit.
4. For non-zero totals, use the **simulated** bKash/Nagad flow with a sample phone such as `01700000000` and payment OTP **`123456`**. This is not an email-recovery code.
5. A valid 100% coupon confirms without payment. Zero-priced categories themselves remain excluded from checkout.
6. Wait for PDF preparation, download the available ticket document and check the intended inbox. Gifts send the PDF to the recipient and a receipt to the buyer.
7. Use **Find my ticket** for email-verified recovery/resend. Resending never resets a used or cancelled ticket.

### Team and admission

1. The owner invites a manager, scanner or viewer by email.
2. The matching verified account accepts and opens **My event teams**.
3. Authorized staff scan a QR or type the ticket ID. Camera access requires HTTPS or a supported local secure context.
4. Admit only after **Entry approved**. Later attempts return **Already checked in**. A network error is not successful admission.

Pausing a coupon invalidates unpaid reservations using it; confirmed tickets remain valid. Cancelling an unused ticket blocks admission but does not perform a refund or rewrite sales history.

## Deployment

| Service | Configuration |
| --- | --- |
| Vercel Hobby | Root `frontend`; frontend and same-origin API forwarding |
| Render Free | Backend container; Gunicorn, Celery account-email consumer and ticket processor in one instance |
| Supabase | PostgreSQL Session pooler and private `tickets` storage bucket |
| Render Key Value | Redis-compatible Valkey; internal connection for hosted services |
| Brevo | HTTPS transactional email with a verified sender |

The hosted application runs with the developer PC off. Idle sleep pauses all processors in the free web instance, and provider quotas apply. Ticket jobs persist in PostgreSQL; free Redis is not durable, so lost account-email messages may require a fresh request. This is a submission/demo setup, not guaranteed always-on hosting.

See [deployment configuration](docs/21-free-submission-deployment.md) for environment variables, proxy settings, persistent storage and verification. Updating GitHub changes the live application only when its hosting project deploys that branch.

## Testing and validation

From `frontend`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run format:check
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Database tests require **isolated PostgreSQL and Redis**, never production/shared Supabase data. Follow [.github/workflows/ci.yml](.github/workflows/ci.yml) for the test environment before running `python -m pytest`. CI enables live browser/API tests with disposable services. Default local browser tests do not establish complete hosted acceptance.

Manual evaluation should cover verification, event submission/approval, normal and 100% coupon purchases, PDF/inbox delivery, recovery, invitations, role revocation, duplicate scanning and reports. Recorded smoke checks do not replace a fresh end-to-end check.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Generic request error after inactivity | Allow backend wake-up and retry; inspect request status/logs if persistent. |
| Redis readiness failure | External TLS URL, current public-IP allowlist and timeout. |
| Database connection failure | Session pooler URI, encoded password and TLS. |
| Verification link only in terminal | Console mode is enabled; configure a real provider for inbox delivery. |
| Paid order but no PDF/email | Running job processor, job attempts, native PDF libraries and email response. |
| Gmail fails on free Render | Use the Brevo HTTPS transport. |
| PowerShell blocks npm | Use `npm.cmd` / `npx.cmd`. |
| Local frontend cannot contact API | Start Django; verify URLs and consistent `127.0.0.1` origins. |
| Camera unavailable | Grant permission over HTTPS or use manual ID with server validation. |

## Security and limitations

- Keep `.env`, database URLs, service/API keys, app passwords, private tickets and backups out of Git.
- Never place server-side keys in `NEXT_PUBLIC_` variables.
- Share evaluator credentials privately; none are included here.
- Real payment settlement, refunds, report exports, production load validation and backup/restore acceptance are outside the current submission scope.
- Fresh hosted purchase-to-inbox-to-phone-check-in acceptance remains a manual check. Email provider acceptance alone does not prove inbox receipt.

## Documentation

- [Design baseline](docs/05-system-design.md) and [requirements decisions](docs/decisions/0001-source-reconciliation.md)
- [Checkout and PDFs](docs/16-phase-2-checkout.md)
- [Venue operations](docs/17-phase-3-venue-operations.md)
- [Recovery](docs/18-ticket-recovery.md)
- [Reporting](docs/19-reporting-and-motion.md)
- [Coupons](docs/20-event-coupons.md)
- [Deployment](docs/21-free-submission-deployment.md)
- [OpenAPI schema](docs/openapi.yaml)

Early notes may contain historical proposals. Use this overview, current implementation and deployment guide for the final setup. The project report contains the detailed development journal.

## Developer team

| Name | Student ID |
| --- | --- |
| Marzan Ahmed | 22201055 |
| Faiza Ahmed Esha | 22201121 |
| Md Daudul Islam | 22201088 |
| Tanjina Akter Nisa | 22201086 |
