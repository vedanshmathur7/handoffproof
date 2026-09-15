# Database contract

## Planned entities

- `workspaces`: tenant boundary.
- `imports`: import metadata, coverage, checksum, and counts.
- `observations`: normalized row and original evidence reference.
- `rules`: immutable reconciliation rule versions.
- `reconciliation_runs`: imports, rule, status, counts, and timestamps.
- `reconciliation_results`: one classified result per eligible source observation.
- `result_candidates`: destination candidates considered.
- `reviews`: append-only human annotations.
- Later `connectors` and `sync_jobs`: encrypted integration metadata and durable jobs.

## Invariants

- Business-data tables contain `workspace_id`.
- IDs are stable UUIDs; timestamps are UTC.
- Runs reference immutable import and rule versions.
- A source observation has at most one final result per run.
- An idempotency key cannot create duplicate runs or results.
- Reviews never rewrite original evidence or machine reasons.

Migrations become authoritative in Task 02. This file must then describe those migrations.
