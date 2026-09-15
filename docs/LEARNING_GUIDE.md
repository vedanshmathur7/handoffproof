# Learning guide

This document grows with the implementation. Each completed phase explains the
idea in simple words, then in technical language, then gives search terms for
independent study.

## Phase 1: Runnable foundation

### Simple explanation

We built the empty shop before putting products inside it:

- FastAPI is the back office where future CSV processing will happen.
- React is the shop screen the user sees.
- PostgreSQL is the cupboard where durable records will live.
- Docker Compose starts the cupboard in the same predictable way on each machine.
- Tests and type checkers act like an inspection checklist.

Example: `/health` is like asking both the receptionist and the storeroom,
“Are you available?” The API returns `ready` only when the process is alive and
PostgreSQL answers a real query.

### Technical flow

1. Uvicorn runs the FastAPI ASGI application.
2. FastAPI resolves the health route's database-check dependency.
3. SQLAlchemy opens an asynchronous Psycopg connection.
4. PostgreSQL executes `SELECT 1`.
5. The API returns HTTP 200 when both components are ready, or HTTP 503 when the
   process is alive but the database is unavailable.
6. Vite serves the React and TypeScript application during development and creates
   optimized static assets during production build.
7. Pytest/Vitest test behavior, Ruff/ESLint check code rules, and mypy/TypeScript
   check types.

### Concepts to learn

- Client-server architecture
- REST APIs and HTTP status codes
- ASGI and asynchronous Python
- Dependency injection
- Database connection and readiness checks
- Environment variables and configuration
- Package managers and lock files
- Containers, Docker Compose, services, volumes, and health checks
- Unit tests, linting, static type checking, and production builds
- CORS between frontend and backend origins

### Search keywords

- `FastAPI beginner REST API tutorial`
- `ASGI vs WSGI simple explanation`
- `FastAPI dependency injection Depends`
- `SQLAlchemy async engine psycopg`
- `HTTP 200 vs 503 health check readiness`
- `React TypeScript Vite beginner`
- `pytest vs ruff vs mypy`
- `Vitest React Testing Library beginner`
- `Docker Compose PostgreSQL healthcheck named volume`
- `package lock file reproducible builds`
- `CORS localhost frontend backend`

### Files worth reading

- Backend entry: `backend/app/main.py`
- Health behavior: `backend/app/api/health.py`
- Backend test: `backend/tests/test_health.py`
- Frontend shell: `frontend/src/App.tsx`
- Frontend test: `frontend/tests/App.test.tsx`
- Local commands: `Makefile`
- PostgreSQL service: `compose.yaml`
