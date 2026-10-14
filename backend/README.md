# Backend

Python 3.12, Django 5.2 LTS, Django REST Framework, PostgreSQL, Celery/Redis. Phase 0 includes the user identity migration, health API, error handling, settings, private storage adapters and payment interface. Authentication and business APIs arrive in later phases.

## Local setup (PowerShell)

For this workstation, follow [development without Docker](../docs/12-cloud-development.md): Supabase PostgreSQL first, then hosted Redis. Use `python manage.py check_services --service database` to verify PostgreSQL independently, or `--service redis` to verify Redis independently. The default checks both.

For the alternative fully local setup, install Docker Desktop or run PostgreSQL 17 and Redis 7 locally. From the repository root:

```powershell
docker compose up -d
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/local.txt
Copy-Item .env.example .env
python manage.py check_services
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

On macOS/Linux use `python3.12 -m venv .venv` and `source .venv/bin/activate`. The ordinary Python installer includes pip. For the Codex bundled runtime on this workstation, use its Python executable to create a venv; if ensurepip fails, run the bundled Python's `-m pip --python .venv/Scripts/python.exe install -r requirements/local.txt` command. Do not install project dependencies into the shared runtime.

URLs: `/api/v1/health/` (process liveness), `/api/v1/schema/` and `/api/v1/docs/` (local only). Liveness does not claim database readiness. `python manage.py check_services` verifies PostgreSQL and Redis separately, returning a nonzero exit code when unavailable. `/api/health` on the frontend checks the backend connection.

The user model is set before the first migration; it uses email login, UUID identity, normalized unique email and Django password hashing. No signup/login endpoints are exposed in this phase.

## Verification

```powershell
ruff check .
black --check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file ../docs/openapi.yaml --validate --fail-on-warn
pytest
```

`pytest tests/test_foundation.py` runs without database services. Full `pytest` also checks the real PostgreSQL unique-email constraint. CI provisions PostgreSQL and Redis. Database/concurrency tests must never be replaced with SQLite or pointed at production.

## Workers

On Linux/WSL/container: `celery -A config worker --loglevel=INFO`. For native Windows development only, try `celery -A config worker --pool=solo --loglevel=INFO`; production uses Linux. Verify delivery with `celery -A config call apps.core.tasks.worker_ping`. The scheduler command will be `celery -A config beat --loglevel=INFO` when schedules are implemented. No ticket/email tasks are implemented yet.

## Storage and hosted settings

Local storage is private beneath `media/`; there is no public media route. The Supabase adapter uses a private bucket and server-only service key. It is implemented but not live-tested because no project exists. Configure `STORAGE_BACKEND=supabase` only after creating a private bucket. Callers must authorize downloads before reading any object. Public banner storage will be introduced with upload validation in Phase 1.

For Supabase Postgres prefer the direct or session-pooler URL for a persistent backend. Transactions use short connections by default, server-side cursors and prepared statements are disabled for pooler compatibility. Production requires DATABASE_URL, explicit hosts, HTTPS frontend origin, a unique long secret, and database TLS. Treat forwarded HTTPS headers as trusted only behind a verified ingress. Cookie JWT/CSRF implementation is Phase 1.

Console email is development-only. Production email fails closed until a transactional provider is configured. The Dockerfile includes WeasyPrint dependencies; rendering remains unverified until the approved Phase 2 PDF mock-up.

## Dependency updates

Edit `requirements/*.in` and use `python -m piptools compile requirements/base.in --output-file requirements/base.txt --strip-extras`, repeating for local and production. Commit the resulting lockfiles; test before updating. All three locks were resolved on Python 3.12; CI validates Linux compatibility.
