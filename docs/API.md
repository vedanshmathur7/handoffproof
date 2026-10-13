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

### `POST /api/v1/reconciliations`

Executes the deterministic engine synchronously. The body identifies one workspace,
source import, destination import, immutable rule, idempotency key, and optional
timezone-aware `evaluated_at`. A new run returns HTTP 201; the same request and key
returns the original run with HTTP 200. Reusing a key for different inputs returns
`IDEMPOTENCY_KEY_REUSED`.

### `GET /api/v1/reconciliations/{run_id}?workspace_id={workspace_id}`

Returns status, combined coverage, rule version, timestamps, and counts for all six
categories.

### `GET /api/v1/reconciliations/{run_id}/results`

Requires `workspace_id`; accepts optional `category`, `offset`, and `limit` (1-100).
Each result contains original source evidence, stable reason code, field differences,
ranked destination candidates, rule details, timestamps, and append-only reviews.

### `POST /api/v1/results/{result_id}/reviews`

Appends reviewer and annotation fields. It never changes the machine category,
reason, or evidence.

### `GET /api/v1/reconciliations/{run_id}/export`

Downloads a CSV containing source ID, category, reason, candidate IDs, differences,
and rule version. Formula-like values are escaped to prevent spreadsheet execution.

### `POST /api/v1/connectors`

Stores a read-only provider configuration in one workspace. The body contains
`workspace_id`, `provider` (`typeform` or `hubspot`), a unique `name`, a write-only
`token`, and, for Typeform only, `typeform.form_id` plus `typeform.field_refs` mapping
exactly `email`, `full_name`, `company`, `region`, and `transfer_enabled` to form
field refs. Typeform connectors are source data; HubSpot connectors are destination
data. Returns HTTP 201 with `credential_configured: true`; the token is never
returned. Errors: `CONNECTOR_CONFIG_INVALID` (422), `CONNECTOR_NAME_TAKEN` (409),
`WORKSPACE_NOT_FOUND` (404), and `CONNECTOR_ENCRYPTION_NOT_CONFIGURED` (503) when
`CONNECTOR_ENCRYPTION_KEYS` is unset or invalid.

### `GET /api/v1/connectors?workspace_id={workspace_id}`

Lists the workspace's connectors without credentials.

### `PUT /api/v1/connectors/{connector_id}/credential`

Replaces the encrypted token (for example after a HubSpot rotation). Body:
`{"workspace_id": "...", "token": "..."}`. Cross-workspace IDs return
`CONNECTOR_NOT_FOUND`.

## Result behavior

Classification follows this fixed order: incomplete coverage, exclusion, open wait
window, identity validity, candidate count, then required-field comparison. The core
uses no network or LLM. Partial or failed coverage always produces `unknown`.

Example complete-fixture counts at `2026-09-02T00:00:00Z`:

```json
{
  "matched": 1,
  "missing": 2,
  "duplicate": 1,
  "field_mismatch": 1,
  "excluded": 1,
  "unknown": 0
}
```

The manifest's partial-coverage case produces
`unknown / DESTINATION_COVERAGE_PARTIAL`. A run against the partial destination
fixture returns six `unknown` results because the whole destination snapshot is
untrustworthy.

Implemented validation errors contain a stable `code`, human-readable `message`,
and optional `details`. Request-validation details never echo submitted input, so
a malformed request cannot reflect a credential back. Request IDs are deferred to Task 07 observability.
