# Development guide

## Requirements

- Python 3.12
- Node.js 24
- `uv`
- Docker with Compose

## Fresh setup

1. Run `cp .env.example .env` from the repository root.
2. Run `make setup` to install locked backend and frontend dependencies.
3. Run `make deps-up` to start PostgreSQL and wait for its health check.
4. Run `make migrate` to apply the latest database schema.
5. Run `make backend-dev` in one terminal; it also applies pending migrations.
6. Run `make frontend-dev` in another terminal.
7. Open `http://localhost:5173`.
8. Request `http://localhost:8000/health`; both process and database should be `ready`.

## Verified commands

- `make setup`: install backend and frontend dependencies.
- `make deps-up`: start PostgreSQL and wait until healthy.
- `make deps-down`: stop PostgreSQL.
- `make migrate`: apply all pending Alembic migrations.
- `make backend-dev`: start FastAPI on port 8000.
- `make frontend-dev`: start Vite on port 5173.
- `make backend-check`: apply migrations, then run backend tests, schema-drift
  detection, linting, and type checking.
- `make frontend-check`: run frontend tests, linting, type checking, and build.
- `make check`: run both complete check suites.

`make demo` points to the local API docs. The browser dashboard also exposes
`Use checked-in sample CSV` for both imports, so the complete workflow can be run
without locating fixture files manually.
