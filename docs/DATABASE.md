# Database contract

Migration `eb584a4dd816` is authoritative for the initial PostgreSQL schema;
later migrations in `backend/migrations/versions/` extend it.

## Implemented entities

- `workspaces`: tenant boundary with UUID, name, and creation time.
- `imports`: source/destination kind, file metadata, checksum, detected schema,
  coverage, status, balanced accepted/rejected counts, and duplicate count.
- `observations`: one normalized CSV row plus immutable original evidence,
  eligibility, rejection reason, and observed time.
- `rules`: immutable workspace-scoped versions containing identity field,
  required fields, exclusions, waiting window, and IANA timezone.
- `reconciliation_runs`: exact source import, destination import, rule version,
  idempotency key, coverage, state, counts, and execution timestamps.
- `reconciliation_results`: exactly one category, reason code, and evidence object
  for a source observation in a run.
- `result_candidates`: ranked destination observations considered for a result.
- `reviews`: append-only reviewer annotations linked to the original result.

- `connectors` (migration `13cf6b01e04d`): workspace-scoped read-only provider
  configuration with provider (`typeform`, `hubspot`), unique name per workspace,
  JSON config (Typeform form ID and field refs), a Fernet-encrypted credential, and
  the credential's last replacement time. Plaintext tokens are never stored.

## Implemented invariants

- Every business-data table contains a non-null `workspace_id`.
- IDs are UUIDs and database-created timestamps use timezone-aware values.
- Composite foreign keys require referenced imports, observations, rules, runs,
  results, and candidates to belong to the same workspace.
- Deleting a workspace cascades through its complete data graph.
- Import row counts must be non-negative and accepted plus rejected must equal total.
- Duplicate rows are counted separately inside rejected rows.
- A checksum can create only one import of a given kind inside a workspace.
- An external record ID is unique inside one import.
- Rule versions are positive and unique inside one workspace.
- Source and destination imports for a run must differ.
- An idempotency key can create only one run inside a workspace.
- A source observation receives at most one result per run.
- A destination observation appears at most once in a result's candidate list.
- Candidate rank is positive.
- Reviews add annotations without changing original evidence or machine reasons.

## PostgreSQL enum values

- Connector provider: `typeform`, `hubspot`
- Import kind: `source`, `destination`
- Coverage: `complete`, `partial`, `failed`
- Import status: `pending`, `completed`, `failed`
- Run status: `pending`, `running`, `completed`, `failed`
- Result category: `matched`, `missing`, `duplicate`, `field_mismatch`,
  `excluded`, `unknown`

## Fixture contracts

Synthetic fixtures live in `backend/tests/fixtures/`. The source and destination
headers are frozen in that directory's README. `fixture_manifest.json` owns the
expected category and reason code for each source record. Task 03 will parse these
files; Task 04 will prove the manifest classifications.
