# TICKETÉ

Event ticketing for Bangladesh. One monorepo with a Django REST Framework backend and a Next.js frontend. Currency: BDT. Timestamps: UTC in storage, Asia/Dhaka in the interface.

## Current status

2026-10-14: design approved; Phase 0 foundation implemented and locally reviewed. The user selected Supabase PostgreSQL and hosted Redis after local Docker setup failed. Follow [development without Docker](docs/12-cloud-development.md). Supabase PostgreSQL connectivity is verified and all 19 initial Django migrations are applied, with none pending. Isolated database tests and Redis/worker integration remain pending. No deployment exists.

Start with the [Phase 0 review](docs/11-phase-0-review.md), [system design](docs/05-system-design.md), and [task breakdown](docs/07-task-breakdown.md). The user confirmed ticket caps per order AND per buyer email across an event; see [decisions](docs/decisions/0001-source-reconciliation.md).

## Structure

- `backend/`: Python 3.12, Django, DRF, PostgreSQL, Celery.
- `frontend/`: Next.js App Router, TypeScript, Tailwind.
- `docs/`: requirements, design, verification, deployment and decisions.
- `docs/source/`: unchanged copies of the supplied requirements and ERD.

## Run locally

Prerequisites: Python 3.12 and Node 24. Follow the [cloud development guide](docs/12-cloud-development.md) for hosted PostgreSQL and Redis without local Docker, then the [backend guide](backend/README.md) and [frontend guide](frontend/README.md). Alternatively, local PostgreSQL 17 and Redis 7 can be started with `docker compose up -d`. Full clean-machine setup awaits verification with working services.

Frontend: `cd frontend`, `npm ci`, `npm run dev`. Open [local preview](http://127.0.0.1:3000) and [design system](http://127.0.0.1:3000/design). Backend process health: `http://127.0.0.1:8000/api/v1/health/`; frontend-to-backend check: `http://127.0.0.1:3000/api/health`.

Current screens are clearly labeled previews. Authentication, event creation, real inventory, dummy checkout and ticket issuance are later phases. No real payments are accepted.

CI configuration runs lint, type checks, production build, browser accessibility tests and PostgreSQL-backed tests when pushed to GitHub. The repository is connected to `MarzzzSiam/TICKETE`; CI results have not yet been verified. Pre-commit hooks are provided; activate the backend venv before `pre-commit install` and before committing.
