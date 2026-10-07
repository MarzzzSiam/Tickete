# Project rules

Status: approved by the user on 2026-10-07.

1. One monorepo, backend/frontend separation, numbered documentation and decision records. Keep source documents unchanged.
2. Feature branches from develop, main stable; Conventional Commits and reviewed pull requests once a remote is configured. Do not claim commits or PRs before they exist.
3. Python 3.12, Django/DRF, Next.js App Router/TypeScript. Verify and pin compatible supported versions during Phase 0; commit lockfiles. No Supabase Auth.
4. Validate and authorize on the server. Event permission matrix is enforced on every object; UI visibility is not access control.
5. Services own business rules and transaction boundaries. Thin views/serializers. No network I/O inside inventory transactions. Decimal BDT and aware UTC timestamps.
6. Every schema change has a migration; inspect constraints and rollback implications. Never apply destructive migrations to a remote database without a reviewed backup/migration plan.
7. No committed secrets, real customer seed data or production OTP logging. Provide environment examples and deterministic fictional demo data.
8. Ruff, Black, ESLint, Prettier, type checks and pre-commit. CI checks backend and frontend separately plus required PostgreSQL integration tests.
9. pytest/pytest-django for services and permission tests; Vitest for meaningful UI logic and Playwright for core journeys. Real PostgreSQL concurrent transactions for stock and scanning races. Target >=80% orders/tickets/checkin coverage.
10. UI uses design tokens. Verify keyboard access, labels, focus, contrast, reduced motion, 360 px mobile and desktop. Provide screenshots at phase review.
11. Update task status, changelog and known limitations with each delivery. Mark untested integrations clearly. No placeholder purchase success, fake metrics, or pretend email delivery in a real flow.
12. Follow the brief's review boundaries: approve design/task plan before application development; review each phase before proceeding; approve ticket HTML before PDF implementation. User instructions can explicitly amend this workflow.
