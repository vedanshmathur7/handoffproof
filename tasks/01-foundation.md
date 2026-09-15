# Task 01: Runnable foundation

## Goal

Create repeatable backend, frontend, PostgreSQL, and verification commands without product behavior.

## Steps

- [x] Record supported Python and Node versions in config.
- [x] Initialize FastAPI, settings, SQLAlchemy, Alembic, pytest, Ruff, and a type checker.
- [x] First add a failing test for `GET /health`; then implement process and database readiness.
- [x] Initialize React, TypeScript, Vite, Vitest, React Testing Library, and linting.
- [x] First add a failing UI test; then render the product name and honest empty state.
- [x] Add PostgreSQL Compose service with health check and named development volume.
- [x] Add root commands for start, test, lint, type-check, build, and later demo loading.
- [x] Make `.env.example` match implemented configuration.
- [x] Run backend tests/lint/types and frontend tests/lint/types/build.
- [x] Start database and apps; request `/health` and open the UI.
- [x] Put only successful commands in the development guide and status.

## Acceptance

- Fresh setup is documented.
- Health proves process and database state.
- Frontend shell renders.
- All configured checks pass.

## Verified on 2026-09-16

- `make setup`: passed and created both dependency lock files.
- `make check`: passed; backend has 2 passing tests and frontend has 1 passing test plus 1 intentionally skipped Task 05 placeholder.
- `make deps-up`: PostgreSQL reached its healthy state.
- Real `GET /health`: returned HTTP 200 with process and database both `ready`.
- Browser inspection: product name and honest empty state rendered correctly.
