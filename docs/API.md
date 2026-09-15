# API contract

`GET /health` is implemented. The remaining surface is planned; Task 03 must replace
its planned shapes with implemented shapes generated from FastAPI's OpenAPI schema.

## Implemented endpoint

### `GET /health`

- HTTP 200: `{"status":"ready","process":"ready","database":"ready"}`
- HTTP 503: `{"status":"degraded","process":"ready","database":"unavailable"}`

The database check executes `SELECT 1`. It does not claim readiness when PostgreSQL
cannot be reached.

## Planned endpoints

- `POST /api/v1/workspaces`: create a demo workspace.
- `POST /api/v1/imports/source`: upload source CSV.
- `POST /api/v1/imports/destination`: upload destination CSV.
- `GET /api/v1/imports/{import_id}`: read status and row counts.
- `POST /api/v1/rules`: create an immutable rule version.
- `POST /api/v1/reconciliations`: execute a comparison.
- `GET /api/v1/reconciliations/{run_id}`: read summary and coverage.
- `GET /api/v1/reconciliations/{run_id}/results`: filter and paginate results.
- `POST /api/v1/results/{result_id}/reviews`: add a review annotation.
- `GET /api/v1/reconciliations/{run_id}/export`: download results.

Every non-2xx response should eventually contain a stable `code`, human-readable `message`, optional `details`, and request ID. Exact schema is unimplemented.
