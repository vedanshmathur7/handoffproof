# Task 02: Database and fixtures

## Goal

Create versioned storage and deterministic data covering every category.

## Steps

- [x] Convert every planned entity in `docs/DATABASE.md` into models.
- [x] Add workspace scoping, UUID keys, UTC timestamps, foreign keys, and uniqueness.
- [x] Create the initial migration; run fresh up, down, and up.
- [x] Define source and destination CSV headers.
- [x] Add valid fixture rows for all six result categories.
- [x] Add incomplete coverage and malformed rows.
- [x] Freeze a manifest mapping source IDs to expected category and reason code.
- [x] Test constraints, cascade behavior, and cross-workspace rejection.
- [x] Update database documentation from the migration.
- [x] Run and record migration and database checks.

## Acceptance

- Migration round trip passes.
- Fixtures cover every category.
- Constraints prevent duplicate and cross-workspace mistakes.

## Verified on 2026-09-17

- Migration `eb584a4dd816` passed `upgrade head -> downgrade base -> upgrade head`.
- `uv run alembic check` reported no schema drift.
- Ten backend tests passed, including constraints, workspace isolation, cascade,
  fixture headers, six categories, partial coverage, and malformed scenarios.
- The full backend and frontend `make check` suite passed.
