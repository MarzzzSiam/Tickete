# TICKETÉ

Event ticketing for Bangladesh. One monorepo with a Django REST Framework backend and a Next.js frontend. Currency: BDT. Timestamps: UTC in storage, Asia/Dhaka in the interface.

## Current status

2026-10-07: design approved; Phase 0 foundation implemented and locally reviewed. Django and Next.js run as a foundation preview. Database services are not available on this workstation, so PostgreSQL migrations, database tests and Redis/worker integration remain pending. Supabase setup is deferred at the user's request. No deployment exists.

Start with the [Phase 0 review](docs/11-phase-0-review.md), [system design](docs/05-system-design.md), and [task breakdown](docs/07-task-breakdown.md). The user confirmed ticket caps per order AND per buyer email across an event; see [decisions](docs/decisions/0001-source-reconciliation.md).

## Structure

- `backend/`: Python 3.12, Django, DRF, PostgreSQL, Celery.
- `frontend/`: Next.js App Router, TypeScript, Tailwind.
- `docs/`: requirements, design, verification, deployment and decisions.
- `docs/source/`: unchanged copies of the supplied requirements and ERD.

## Run locally

Prerequisites: Python 3.12, Node 24 and Docker Desktop (or local PostgreSQL 17 and Redis 7). Start services with `docker compose up -d`, then follow the [backend guide](backend/README.md) and [frontend guide](frontend/README.md). Full clean-machine setup awaits verification on a machine with those services.

Frontend: `cd frontend`, `npm ci`, `npm run dev`. Open [local preview](http://127.0.0.1:3000) and [design system](http://127.0.0.1:3000/design). Backend process health: `http://127.0.0.1:8000/api/v1/health/`; frontend-to-backend check: `http://127.0.0.1:3000/api/health`.

Current screens are clearly labeled previews. Authentication, event creation, real inventory, dummy checkout and ticket issuance are later phases. No real payments are accepted.

CI configuration runs lint, type checks, production build, browser accessibility tests and PostgreSQL-backed tests when pushed to a GitHub remote. No remote has been configured, so CI execution is not claimed. Pre-commit hooks are provided; activate the backend venv before `pre-commit install` and before committing.
