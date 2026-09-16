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

## Phase 2: Database schema and deterministic fixtures

### Simple explanation

We designed labelled cupboards before storing real workflow data:

- A workspace is one company's locked room.
- An import is one CSV delivery box.
- An observation is one row taken from that box.
- A rule says how two rows should be compared.
- A run records one comparison job.
- A result records the final category and reason.
- Candidates show which destination rows were considered.
- Reviews preserve a human comment without changing the machine result.

Example: suppose Company A and Company B both have a lead called
`mira@example.test`. Every row also carries its `workspace_id`, and composite
foreign keys prevent Company B's run from pointing at Company A's import.

### Technical flow

1. SQLAlchemy models define Python-side entities, columns, types, and constraints.
2. Alembic migration `eb584a4dd816` creates the same schema in PostgreSQL.
3. UUID primary keys give records stable identifiers.
4. Timezone-aware columns store database timestamps consistently.
5. Composite foreign keys enforce workspace ownership in PostgreSQL.
6. Unique and check constraints reject duplicate IDs, repeated idempotency keys,
   invalid counts, and other impossible states.
7. `ON DELETE CASCADE` removes a deleted workspace's dependent graph.
8. Synthetic CSV files and a JSON manifest freeze expected inputs and outcomes.
9. Tests prove constraints, cross-workspace rejection, cascades, headers, all six
   categories, partial coverage, and malformed-row scenarios.

### Concepts to learn

- Relational database schema design
- Primary keys, foreign keys, composite foreign keys, and unique constraints
- Check constraints and database invariants
- Multi-tenant workspace isolation
- UUIDs and timezone-aware timestamps
- PostgreSQL enum and JSONB columns
- SQLAlchemy 2 declarative models
- Alembic migrations and schema drift
- Migration upgrade/downgrade round trips
- Cascading deletes
- Deterministic test fixtures and golden manifests
- Idempotency keys

### Search keywords

- `relational database primary key foreign key beginner`
- `composite foreign key multi tenant PostgreSQL`
- `PostgreSQL check constraint unique constraint`
- `SQLAlchemy 2 mapped_column tutorial`
- `Alembic migration upgrade downgrade tutorial`
- `Alembic check schema drift`
- `PostgreSQL UUID timezone timestamp JSONB enum`
- `ON DELETE CASCADE explained`
- `SaaS tenant isolation workspace_id`
- `idempotency key API database`
- `golden test fixtures manifest`

### Files worth reading

- ORM schema: `backend/app/models.py`
- Database base/session: `backend/app/database.py`
- Initial migration: `backend/migrations/versions/eb584a4dd816_initial_schema.py`
- Constraint tests: `backend/tests/test_database.py`
- Fixture contract tests: `backend/tests/test_fixtures.py`
- Synthetic data: `backend/tests/fixtures/`
- Schema contract: `docs/DATABASE.md`
