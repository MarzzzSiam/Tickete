# Development without Docker

Decision, 2026-10-14: use hosted Supabase PostgreSQL and hosted Redis. Django and Next.js continue running on this Windows workstation. A Linux Celery worker will be configured after both connections work. Supabase connectivity is verified with TLS required by the client. All 19 initial Django migrations applied successfully and the migration check reports none pending. Redis, the worker and isolated database tests are pending.

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

Next.js and Django can run locally while the worker is pending. Storage integration, transactional email and production deployment are separate remaining setup tasks. No real payments or production data belong in this development project.

## References

- [Supabase PostgreSQL connection methods](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Render Key Value connections, access control and persistence](https://render.com/docs/key-value)
- [Celery Redis TLS configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-backend)
- [Render background workers](https://render.com/docs/background-workers)
