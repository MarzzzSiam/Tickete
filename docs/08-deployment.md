# Deployment plan

2026-10-25: free submission deployment is being prepared; follow the [current deployment configuration](21-free-submission-deployment.md). Public URLs and live acceptance are still pending. The rest of this document records the original production planning considerations.

Local: isolated development database, fictional fixtures, dummy gateway and console email. Staging: separate database, storage buckets, secrets, sender and approved testers. Production: paid capacity chosen from measured load, verified domain and backups. Never point development tests at production.

Environment inventory to formalize in Phase 0: DATABASE_URL, SECRET_KEY, ALLOWED_HOSTS, FRONTEND_ORIGIN, CSRF_TRUSTED_ORIGINS, REDIS_URL, gateway choice, storage project/bucket credentials, email provider key/from address, support email and frontend API URL. Only explicitly public values may use NEXT_PUBLIC prefixes.

Before deployment verify supported Supabase connection/pooler mode, TLS, Django connection lifetime and server-side cursor compatibility from current official documentation. Choose sibling application/API domains or another tested topology for cookie authentication. Do not assume third-party cookies work across default hosting domains.

Backend Docker image must include WeasyPrint native libraries and fonts. Processes: web, Celery worker and a single scheduler. Exact commands will be tested after scaffolding. Readiness should check required dependencies without revealing credentials.

Release procedure: staging tests, backup, inspect migration plan, run compatible migrations once, deploy backend/workers/frontend, smoke-test and monitor. Roll back application versions only when schema-compatible; destructive migration reversal requires a restore plan. Define retention, recovery objectives and test restore before pilot launch.
