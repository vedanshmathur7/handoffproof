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

## Live shadow check (Task 06, manual)

Use only consented test accounts and synthetic leads. Never commit tokens or exports.

1. Put a generated Fernet key in the local `.env` as `CONNECTOR_ENCRYPTION_KEYS`.
2. Typeform: create a personal access token with only `responses:read`. HubSpot:
   create a private app with only `crm.objects.contacts.read`.
3. Start the API (`make backend-dev`), create a workspace, then `POST
   /api/v1/connectors` once for Typeform (with `form_id` and `field_refs`) and once
   for HubSpot. Tokens go only in those request bodies.
4. Wait at least 30 minutes after the last test submission (Typeform indexing delay),
   then `POST /api/v1/shadow-syncs` with `full_resync: true`.
5. Create a rule from the two returned import IDs and run `POST
   /api/v1/reconciliations` with the returned `evaluated_at`.
6. Before looking at the product results, write a manual audit sheet: one expected
   category per test response. Then compare it row by row with the export.
