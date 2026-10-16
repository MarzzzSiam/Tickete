# Development without Docker

Decision, 2026-10-14: use hosted Supabase PostgreSQL and hosted Redis. Django and Next.js continue running on this Windows workstation. Supabase connectivity is verified with TLS required by the client. All 19 initial Django migrations applied successfully and the migration check reports none pending. Update, 2026-10-16: hosted Redis PING succeeded after allow-list troubleshooting; hosted-worker settings pass Django checks. The live task/result check failed, so worker deployment and execution remain unverified. Isolated database tests are also pending.

## 1. Supabase development database

1. Create a project named `tickete-dev` in the [Supabase dashboard](https://supabase.com/dashboard). Choose a nearby region, such as Singapore if offered. Save the database password in your password manager.
2. Disable the project's Data API in its API settings for this Django-only database. Django manages authorization and connects directly using PostgreSQL. Do this before migrations: Django-created tables do not automatically receive Supabase RLS policies. Supabase Auth is not used.
3. Open **Connect**, select **Session pooler**, and copy its PostgreSQL URI (port 5432). Use the exact supplied host and username. Session pooling supports IPv4 networks.
4. In `backend/.env`, replace only `DATABASE_URL` with this URI. Replace the password placeholder with the database password, percent-encoding reserved characters in the password. Add `?sslmode=require` (or `&sslmode=require` if the URI already contains a query). Keep this file private and ignored by Git. Never put database credentials in the frontend or chat.
5. Keep `DJANGO_SETTINGS_MODULE=config.settings.local` while the web application runs locally. Leave storage local for now; database access does not need a Supabase service key.

From the repository root, using the existing virtual environment:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check_services --service database
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
```

Run migrations only after confirming this is the new development project. Do not create the ERD tables manually; Django migrations own the application schema. Do not run the full test suite against this shared database: database tests need an isolated test database and suitable permissions. CI already supplies isolated PostgreSQL.

## 2. Hosted Redis

Create a development **Key Value** instance on Render, reviewing its displayed cost before creation. Choose `noeviction` because this instance carries Celery jobs. Free instances do not persist queued data across restarts and are suitable only for disposable development work.

Allow external access only from your current public IP (`/32` for a single IPv4 address). Copy the external `rediss://` connection URI into `REDIS_URL` in `backend/.env`. Add `?ssl_cert_reqs=required`, or append it with `&` when a query already exists. This enables certificate verification for Celery and redis-py. Preserve all existing URI credentials and options. Update the allow list if your public IP changes.

```powershell
.\.venv\Scripts\python.exe manage.py check_services
```

Both services must report ready. A database-only check does not establish Redis or worker readiness.

## 3. Background worker and remaining verification

A hosted Linux Celery worker is a separate process, not something supplied by Supabase or Redis. Configure it after selecting a hosting plan and connecting Redis; it may incur a separate charge. It must use the same development database and queue as the local API. A Render worker can use the Key Value internal connection in the same region. Deployment settings, Python 3.12 dependencies and worker environment still require configuration and validation before deployment.

The worker command, run from `backend`, is `celery -A config worker --loglevel=INFO`. Verify that `apps.core.tasks.worker_ping` actually completes; publishing a task alone is insufficient. Native Windows Celery is not the supported deployment path. Ticket generation and email jobs remain later phases.

### Render dashboard setup

First create a Render account and choose **New > Key Value**:

| Field | Value |
|---|---|
| Name | `tickete-dev-redis` |
| Region | Singapore if available; use the same region for the worker |
| Maxmemory policy | `noeviction` |
| Plan | Review the displayed cost; use persistence for anything beyond disposable tests |

Render currently uses Redis-compatible Valkey for new Key Value instances. Once available, configure the IP allow list and save the external TLS URI in the local `.env` as described above. Do not use its internal URI from Windows.

After Redis readiness passes, create **New > Background Worker**, connect `MarzzzSiam/TICKETE`, and use these settings. The worker code must first be pushed to the selected branch. Review the displayed recurring worker cost before creating it.

| Field | Value |
|---|---|
| Name | `tickete-dev-worker` |
| Branch | `codex/hosted-worker-setup` for initial verification; switch to `main` after merge |
| Root directory | `backend` |
| Language/runtime | Python 3 |
| Build command | `pip install -r requirements/production.txt` |
| Start command | `celery -A config worker --loglevel=INFO --concurrency=1` |
| Region | Same as Key Value |

Set environment variables in Render's dashboard, not in Git:

- `PYTHON_VERSION`: `3.12.14` (the version used for this foundation).
- `DJANGO_SETTINGS_MODULE`: `config.settings.worker`.
- `SECRET_KEY`: copy the generated value from the private development `.env`.
- `DATABASE_URL`: the same Supabase development Session pooler URI, with `sslmode=require`.
- `REDIS_URL`: the Key Value internal URI for this worker in the same Render region. The local API uses the external URI to the same instance.

Worker settings disable debug, require explicit credentials, enforce PostgreSQL TLS and leave email disabled until its provider is integrated. No web service, public worker URL or Supabase GitHub integration is required. Native Python deployment of PDF rendering dependencies remains a separate Phase 2 check.

From `backend` on Windows, verify the live task after deployment:

```powershell
.\.venv\Scripts\python.exe manage.py check_services
.\.venv\Scripts\python.exe manage.py check_worker --timeout 30
```

Only `Celery: task completed and result verified` proves the queue, worker execution and result backend worked together. The command sends a harmless expiring task and reports failures without connection credentials.

Next.js and Django can run locally while the worker is pending. Storage integration, transactional email and production deployment are separate remaining setup tasks. No real payments or production data belong in this development project.

## References

- [Supabase PostgreSQL connection methods](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Render Key Value connections, access control and persistence](https://render.com/docs/key-value)
- [Celery Redis TLS configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-backend)
- [Render background workers](https://render.com/docs/background-workers)
