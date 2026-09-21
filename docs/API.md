# API contract

The canonical machine-readable contract is generated from FastAPI at
`docs/openapi.json`. Run `make api-docs` after changing routes or schemas.

## Implemented endpoints

### `GET /health`

- HTTP 200: `{"status":"ready","process":"ready","database":"ready"}`
- HTTP 503: `{"status":"degraded","process":"ready","database":"unavailable"}`

The database check executes `SELECT 1`. It does not claim readiness when PostgreSQL
cannot be reached.

### `POST /api/v1/workspaces`

Creates an isolated demo workspace. Body: `{"name":"Interview demo"}`. Returns
HTTP 201 with its UUID, name, and UTC creation timestamp.

### `POST /api/v1/imports/source`

### `POST /api/v1/imports/destination`

Both accept multipart fields `workspace_id`, `file`, and optional `coverage`
(`complete`, `partial`, or `failed`). Uploads are limited to 1 MB and fixed UTF-8
CSV schemas. A new import returns HTTP 201; a repeated byte-identical upload returns
the existing import with HTTP 200.

The response includes `total_rows`, `accepted_rows`, `rejected_rows`,
`duplicate_rows`, `schema_fields`, coverage, status, and stable row errors. Example:

```json
{
  "kind": "source",
  "coverage": "failed",
  "status": "failed",
  "total_rows": 4,
  "accepted_rows": 0,
  "rejected_rows": 4,
  "duplicate_rows": 0,
  "row_errors": [
    {"row_number": 2, "code": "MISSING_SOURCE_RECORD_ID"}
  ]
}
```

### `GET /api/v1/imports/{import_id}?workspace_id={workspace_id}`

Returns import status and counts only when the import belongs to the supplied
workspace. Cross-workspace reads return `IMPORT_NOT_FOUND`.

### `POST /api/v1/rules`

Creates a new immutable version. Identity and required fields must exist in both
imports; eligibility must exist in the source; timezone must be an IANA name.

```json
{
  "workspace_id": "00000000-0000-0000-0000-000000000001",
  "source_import_id": "00000000-0000-0000-0000-000000000002",
  "destination_import_id": "00000000-0000-0000-0000-000000000003",
  "name": "Email handoff",
  "eligibility": {"field": "transfer_enabled", "equals": "true"},
  "identity_field": "email",
  "required_fields": ["full_name", "company", "region"],
  "wait_seconds": 300,
  "timezone": "UTC"
}
```

## Planned endpoints

- `POST /api/v1/reconciliations`: execute a comparison.
- `GET /api/v1/reconciliations/{run_id}`: read summary and coverage.
- `GET /api/v1/reconciliations/{run_id}/results`: filter and paginate results.
- `POST /api/v1/results/{result_id}/reviews`: add a review annotation.
- `GET /api/v1/reconciliations/{run_id}/export`: download results.

Implemented validation errors contain a stable `code`, human-readable `message`,
and optional `details`. Request IDs are deferred to Task 07 observability.
