# Free submission deployment

2026-10-26: frontend and API deployed; live authentication checks passed.

- Website: https://tickete-ten.vercel.app
- API: https://tickete-api.onrender.com/api/v1/health/
- Vercel project: `marzzz1/tickete`, Hobby, production branch `main`.
- Render: `tickete-api`, Free, Singapore, service `srv-dbf4gkavcj2c73eq8s70`.
- Six local media files copied to the private Supabase bucket and byte-verified.
- [Deployment CI](https://github.com/MarzzzSiam/TICKETE/actions/runs/40218861071) passed,
  including the Docker build. Next.js is patched to 16.4.3.
- Brevo accepted one approved sample PDF email; recipient inbox confirmation remains external.
- Hosted Celery completed a worker ping. Public events and a stored banner load correctly.
- The API proxy explicitly appends Django endpoint slashes and preserves the slashless PDF route.
- Verified application revision: `5d9271f`. Signup, login, authenticated profile, logout
  and session clearing passed through the public Vercel origin. Cookie Secure,
  HttpOnly and SameSite=Lax flags were checked. The temporary account was removed.
- Checkout ticket/category/coupon controls render on the deployed site. A fresh full
  hosted purchase-to-email-to-check-in has not been performed; existing event stock
  was not consumed for deployment verification.

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

- `ALLOWED_HOSTS=tickete-api.onrender.com`.
- `FRONTEND_ORIGIN=https://tickete-ten.vercel.app` (no trailing slash).
- `SECRET_KEY`: new strong secret (at least 50 characters), not the local development key.
- `DATABASE_URL`: Supabase session pooler URL with `sslmode=require`.
- `REDIS_URL`: existing Redis/Valkey connection URL.
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: server-only Storage credentials.
- `STORAGE_BACKEND=supabase`, `SUPABASE_PRIVATE_BUCKET=tickets`.
- `EMAIL_PROVIDER=brevo`, `BREVO_API_KEY`: verified sender's HTTP API key, not SMTP key.
- `DEFAULT_FROM_EMAIL=TICKETÉ <hello.tickete@gmail.com>` and matching support email.
- `TRUST_PROXY_SSL_HEADER=True`, `DJANGO_SETTINGS_MODULE=config.settings.production`.

Vercel (production environment):

- `BACKEND_ORIGIN=https://tickete-api.onrender.com`
- `API_BASE_URL=https://tickete-api.onrender.com/api/v1`
- `NEXT_PUBLIC_API_BASE_URL=/api/v1`

The browser uses a same-origin Next.js rewrite so secure authentication cookies stay
first-party. Server-side event requests use the absolute API address. API trailing
slashes are preserved. Redeploy Vercel after changing these build-time settings.

The Docker entrypoint applies migrations before starting services. No public media
directory is served; private files continue through authenticated API endpoints.
Existing local banners/PDF files must be copied to the private bucket with their
existing relative keys before switching storage, without changing ownership or ACLs.

## Verification record and final manual acceptance

- Verified: API/proxy health, frontend and approved events load over HTTPS.
- Verified: existing event banner loads from persistent Storage.
- Verified: signup/login/logout and CSRF through the frontend proxy.
- Verified: background worker ping and Brevo acceptance of the approved sample PDF.
- Manual: recipient confirms inbox receipt; complete a fresh simulated purchase,
  download its PDF and check it in once, then confirm duplicate-entry rejection.
- Manual: verification/reset links and organizer reports with the owner's account.
- No paid resource, real payment gateway or local-PC dependency was introduced.
- Actual URLs, tested revision and free-tier limitations are recorded in README.

References: [Render free limits](https://render.com/docs/free),
[Brevo attachment API](https://developers.brevo.com/reference/send-transac-email).
