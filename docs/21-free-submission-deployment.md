# Free submission deployment

2026-10-25: deployment preparation in progress. No public URL has been verified yet.

## Services

- Vercel Hobby: frontend, root directory `frontend`, Node 24, build `npm run build`.
- Render Free web service: `backend/Dockerfile`, Singapore; gunicorn plus a single
  Celery account-email consumer and the durable ticket job processor in the same instance.
- Existing Supabase Postgres and a **private** `tickets` Storage bucket.
- Existing Render Key Value instance, preferably its internal URL in the same region.
- Brevo HTTPS API for mail, including PDF attachments. Gmail SMTP remains local only.

This is a submission/demo topology, not guaranteed always-on production hosting.
Render sleeps after 15 minutes without traffic. Jobs stop while asleep and resume
when a request wakes the API; first access may take about a minute. No PC worker
is needed. Render free memory and monthly hours, Supabase storage/database quotas,
Vercel Hobby terms and Brevo daily sending limits still apply. Do not enable paid plans.
The free Redis instance is not a durable queue: account email requests may need to
be requested again after a Redis restart. Ticket delivery jobs are held in Postgres.

## Configuration

Deploy the current tested branch, not an older default branch. The root `render.yaml`
declares only a free web service and prompts for private environment variables.
Never commit `.env`, service keys, email API keys, passwords or live connection URLs.

Render:

- `ALLOWED_HOSTS`: exact Render API hostname, without scheme.
- `FRONTEND_ORIGIN`: stable Vercel production URL, including `https://`, no trailing slash.
- `SECRET_KEY`: new strong secret (at least 50 characters), not the local development key.
- `DATABASE_URL`: Supabase session pooler URL with `sslmode=require`.
- `REDIS_URL`: existing Redis/Valkey connection URL.
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: server-only Storage credentials.
- `STORAGE_BACKEND=supabase`, `SUPABASE_PRIVATE_BUCKET=tickets`.
- `EMAIL_PROVIDER=brevo`, `BREVO_API_KEY`: verified sender's HTTP API key, not SMTP key.
- `DEFAULT_FROM_EMAIL=TICKETÉ <hello.tickete@gmail.com>` and matching support email.
- `TRUST_PROXY_SSL_HEADER=True`, `DJANGO_SETTINGS_MODULE=config.settings.production`.

Vercel (production environment):

- `BACKEND_ORIGIN=https://<actual-api-host>`
- `API_BASE_URL=https://<actual-api-host>/api/v1`
- `NEXT_PUBLIC_API_BASE_URL=/api/v1`

The browser uses a same-origin Next.js rewrite so secure authentication cookies stay
first-party. Server-side event requests use the absolute API address. API trailing
slashes are preserved. Redeploy Vercel after changing these build-time settings.

The Docker entrypoint applies migrations before starting services. No public media
directory is served; private files continue through authenticated API endpoints.
Existing local banners/PDF files must be copied to the private bucket with their
existing relative keys before switching storage, without changing ownership or ACLs.

## Acceptance before submission

- API health, frontend and approved events load over HTTPS.
- Existing banners load from persistent Storage.
- Signup/login/logout, verification and CSRF work through the frontend proxy.
- Test purchase confirms, stock/caps apply, PDF downloads and arrives by email.
- Organizer reports and volunteer check-in reject a reused ticket.
- No paid resource, real payment gateway or local-PC dependency is introduced.
- Record actual URLs, tested revision and outstanding limitations in README.

References: [Render free limits](https://render.com/docs/free),
[Brevo attachment API](https://developers.brevo.com/reference/send-transac-email).
