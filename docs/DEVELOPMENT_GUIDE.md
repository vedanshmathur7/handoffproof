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
4. Run `make backend-dev` in one terminal.
5. Run `make frontend-dev` in another terminal.
6. Open `http://localhost:5173`.
7. Request `http://localhost:8000/health`; both process and database should be `ready`.

## Verified commands

- `make setup`: install backend and frontend dependencies.
- `make deps-up`: start PostgreSQL and wait until healthy.
- `make deps-down`: stop PostgreSQL.
- `make backend-dev`: start FastAPI on port 8000.
- `make frontend-dev`: start Vite on port 5173.
- `make backend-check`: run backend tests, linting, and type checking.
- `make frontend-check`: run frontend tests, linting, type checking, and build.
- `make check`: run both complete check suites.

`make demo` currently explains that demo fixtures arrive in Task 02; it does not load data yet.
