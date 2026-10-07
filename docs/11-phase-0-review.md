# Phase 0 review — 2026-10-07

## Delivered

One monorepo, Python 3.12/Django backend and Next.js/React/TypeScript frontend. The source docs and logos are preserved. Brand tokens, serif/sans/mono fonts, buttons, fields, select/checkbox, cards, ticket preview, badges, quantity stepper, mobile drawer/dialog, toast, table, empty and loading states are available for visual review.

The landing page uses the supplied artwork and original CSS ticket illustrations. It does not fabricate sales statistics or offer working checkout. `/events` and `/start` explain current availability; `/design` is an interactive review gallery. Favicon artwork is an SVG viewport around the unchanged supplied raster icon, not a newly drawn logo. Generic Open Graph metadata uses the supplied horizontal logo; event-specific banner/title previews arrive in Phase 1.

Backend exposes a process health API and local Swagger/OpenAPI. The initial custom user model is defined before the first migration. Storage and gateway boundaries are in place, but no payment or ticket functionality is implemented. Default API permissions deny access unless an endpoint opts in; authentication endpoints arrive in Phase 1.

## Verification actually performed

| Check | Result |
|---|---|
| Python runtime | Bundled Python 3.12.14; isolated project venv |
| Django system checks / Ruff | Passed |
| Black formatting | Applied and checked |
| Backend non-database tests | 11 passed |
| OpenAPI generation and validation | Passed; saved `docs/openapi.yaml` |
| Frontend ESLint / TypeScript / Prettier | Passed |
| Next.js production build | Passed |
| Playwright desktop 1440 px / mobile 360 px | 5 passed, 1 intentional desktop skip of mobile-only menu test |
| Axe WCAG A/AA checks on landing and design | No violations detected |
| Exact mobile viewport overflow | Passed after clipping decorative orbit artwork |
| Frontend `/api/health` -> Django | Returned status ok and service tickete-api |
| npm production dependency audit | 0 vulnerabilities reported |
| PostgreSQL / Redis readiness | Failed: neither service available locally |

Automated accessibility checks are not a complete accessibility certification. Browsers tested: Chromium desktop and mobile emulation, not physical phones or Safari. UI screenshots were visually inspected. No performance score or clean-machine setup duration is claimed.

Screenshots: [landing desktop](screenshots/landing-desktop.png), [landing mobile](screenshots/landing-mobile.png), [design desktop](screenshots/design-desktop.png), [design mobile](screenshots/design-mobile.png).

## Local preview

Frontend: http://127.0.0.1:3000. Design gallery: http://127.0.0.1:3000/design. API: http://127.0.0.1:8000/api/v1/health/. These development servers run only while the local processes remain active.

The API preview was started using Python's local WSGI development server without Django's migration startup check so process-only health can be reviewed without a database. This does not simulate or bypass database-backed behavior: those routes do not exist yet. Once PostgreSQL is available, use the normal migrate/runserver steps in `backend/README.md`.

## Remaining Phase 0 acceptance work

1. Install/start Docker Desktop or provision local PostgreSQL 17 and Redis 7. Run `docker compose up -d`, readiness checks, migrations and full pytest, including the two database identity tests.
2. Verify a Celery task through the live Redis broker; build/test the Docker image and Linux lockfile compatibility. CI is defined but has not run because no GitHub remote is configured.
3. Connect Supabase when the user creates a project. Live database/storage credentials were neither requested in chat nor invented. Supabase adapter has not been integration-tested.
4. Obtain user approval of the desktop/mobile visual direction. Phase 1 has not started.

## Dependency finding

The development dependency audit reports five high-severity entries from the same `braces <=3.0.3` advisory through micromatch/fast-glob in eslint-config-next. Registry lookup reports 3.0.3 as the latest braces release. npm suggests downgrading eslint-config-next to 14, which does not match this Next.js 16 project; that change was not made blindly. The production dependency audit is clean. Recheck the advisory before CI runs on untrusted pattern inputs and before launch; avoid presenting all dependencies as vulnerability-free. ESLint 9 also emits a support deprecation notice; revisit once the framework lint stack supports a newer major.

## Documentation references consulted

- [Django 5.2 Python support](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Next.js App Router installation](https://nextjs.org/docs/app/getting-started/installation)
- [Supabase PostgreSQL connections](https://supabase.com/docs/guides/database/connecting-to-postgres)
- Installed Next.js 16.4 documentation for fonts, route handlers and metadata, under `frontend/node_modules/next/dist/docs`.

The remaining production hardening, provider integrations and full sales/check-in concurrency tests belong to later phases and are not claimed complete.
