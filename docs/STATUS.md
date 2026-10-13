# Current status

- Current phase: Live integration
- Active task: `tasks/06-live-connectors.md`
- Working name: HandoffProof
- Verified workflows: 1/2 (`CSV -> reconciliation -> dashboard`, `Typeform -> HubSpot shadow check`)
- Completed tasks: 6/9
- Working application: complete CSV workflow is usable through the browser and API

## Completed and verified

- Market decision artifacts exist in `research/`.
- Scope, requirements, architecture, ownership map, task sequence, and placeholders were created.
- Task 00 passed its documentation, task-presence, placeholder-presence, and terminology checks.
- Task 01 created locked Python/Node environments, FastAPI, React, PostgreSQL Compose, root commands, and an honest UI shell.
- `GET /health` verifies both the API process and a real PostgreSQL connection.
- Private GitHub repository `vedanshmathur7/handoffproof` tracks the project, and CI
  runs the backend and frontend checks on every push and pull request.
- Task 02 implemented all eight planned PostgreSQL entities, workspace-scoped
  constraints, the initial migration, and deterministic synthetic fixtures.
- Task 03 implemented demo workspaces, strict source/destination CSV imports,
  row evidence and stable errors, coverage counts, idempotency, and versioned rules.
- Task 04 implemented deterministic reconciliation, atomic/idempotent runs, ranked
  candidates, evidence, filters, reviews, and safe CSV export.
- Task 05 implemented the guided reviewer dashboard, canonical sample buttons,
  coverage warnings, filters, evidence inspection, review notes, and export access.

## In progress

- Task 06 has an in-process read-only connector foundation. Typeform uses a
  five-minute overlap window and response-ID deduplication; HubSpot follows its
  cursor pagination. Both convert provider records into the existing normalized
  import contract before reconciliation.
- Official Typeform and HubSpot behavior was verified on 2026-10-13 and recorded
  in `docs/ARCHITECTURE.md`. Typeform pages by response `token`, its checkpoint
  stops 30 minutes before read time for indexing delay, and both clients space
  requests and honor `Retry-After` within bounded retries.
- Connector credentials are stored per workspace in `connectors`, encrypted with
  rotatable Fernet keys, never returned by the API, never echoed in validation
  errors, and absent from captured logs. Missing keys fail closed with HTTP 503.
- `POST /api/v1/shadow-syncs` manually reads Typeform then HubSpot (GET only),
  stores both snapshots as ordinary imports, and records workspace-scoped
  `connector_syncs` checkpoints. Checkpoints advance only after complete reads;
  stale checkpoints, throttling, auth failures, and missing destination data
  produce partial or failed coverage, and the engine then returns `unknown`.
- Connector mocks prove bounded retry, throttling to partial coverage, no
  write-capable HTTP method, and a Typeform-to-HubSpot snapshot reaching the same
  deterministic engine as CSV imports.

## Blockers

- None for documentation validation.
- Completing Task 06 needs consented Typeform and HubSpot test accounts with
  least-privilege read tokens and a manual audit of their records. These must be
  provided by the project owner; no live result has been invented.

## Checks actually run

- Repository inspection on 2026-09-16 found four research artifacts before scaffolding.
- `test -f AGENTS.md && test -f docs/STATUS.md && test -f docs/PLAN.md`: passed.
- Task discovery listed exactly Tasks 00 through 08.
- Placeholder discovery listed backend and frontend files successfully.
- Scope/category search found no conflicting product behavior; expected references were consistent.
- `make setup`: passed and generated `backend/uv.lock` and `frontend/package-lock.json`.
- `make check`: passed with 2 backend tests, 1 frontend test, linting, type checks, and a production frontend build. One Task 05 placeholder suite is intentionally skipped.
- Docker Compose PostgreSQL: healthy.
- Real `GET /health`: HTTP 200 with process and database both `ready`.
- Browser inspection: HandoffProof heading and the empty-state message rendered correctly.
- GitHub Actions CI run #1: passed in 33 seconds for commit `8aeb7a2`.
- Migration `eb584a4dd816` passed upgrade, downgrade, and fresh re-upgrade.
- `uv run alembic check`: no schema drift detected.
- `make check`: passed with 10 backend tests, backend lint/types/schema checks,
  1 frontend test, frontend lint/types, and a production build.
- Migration `382806336a30` passed downgrade, upgrade, and schema-drift checks.
- `make check`: passed with 16 backend tests, backend lint/types/schema checks,
  1 frontend test, frontend lint/types, and a production build. The Task 05 suite
  remains intentionally skipped.
- Task 04 focused checks passed 28 backend tests, Ruff, mypy, and Alembic drift.
- Task 05 frontend checks passed 5 tests, ESLint, TypeScript, and production build.
- Chrome completed the sample workflow with 6 accepted source rows, 4 accepted
  destination rows, and counts 1 matched, 2 missing, 1 duplicate, 1 mismatch,
  1 excluded, and 0 unknown. Evidence and an append-only review were visible.
- Task 06 connector-focused checks passed on 2026-10-13: 4 mocked connector and
  engine-contract tests, Ruff, and mypy. Local PostgreSQL was started only for the
  database-backed engine-contract test; no live provider request was sent.
- Full `make check` passed on 2026-10-13: 32 backend tests, Alembic drift check,
  backend lint/types, 5 frontend tests, frontend lint/types, and production build.

- Provider-verification checks on 2026-10-13: 4 connector tests, then full
  `make check` (32 backend tests, Alembic drift, Ruff, mypy, 5 frontend tests,
  ESLint, TypeScript, production build) passed.

- Credential-storage checks on 2026-10-13: migration `13cf6b01e04d` upgrade,
  downgrade, re-upgrade, and drift check passed; full `make check` passed with
  36 backend tests, Ruff, mypy, 5 frontend tests, ESLint, TypeScript, and build.

- Shadow-sync checks on 2026-10-13: migration `ec25da27f28a` upgrade, downgrade,
  re-upgrade, and drift check passed; 5 mocked shadow-sync API tests passed; full
  `make check` passed with 41 backend tests, Ruff, mypy, 5 frontend tests, ESLint,
  TypeScript, and production build. No live provider request has been sent.

## Next three actions

1. Obtain consented Typeform and HubSpot test accounts with `responses:read` and
   `crm.objects.contacts.read` tokens, kept only in a local `.env`/API call.
2. Run a live manual shadow sync and reconciliation on adjudicated test records.
3. Compare product results with a manual audit and complete Task 06 acceptance.
