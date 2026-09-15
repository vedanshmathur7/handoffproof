# Task 02: Database and fixtures

## Goal

Create versioned storage and deterministic data covering every category.

## Steps

- [ ] Convert every planned entity in `docs/DATABASE.md` into models.
- [ ] Add workspace scoping, UUID keys, UTC timestamps, foreign keys, and uniqueness.
- [ ] Create the initial migration; run fresh up, down, and up.
- [ ] Define source and destination CSV headers.
- [ ] Add valid fixture rows for all six result categories.
- [ ] Add incomplete coverage and malformed rows.
- [ ] Freeze a manifest mapping source IDs to expected category and reason code.
- [ ] Test constraints, cascade behavior, and cross-workspace rejection.
- [ ] Update database documentation from the migration.
- [ ] Run and record migration and database checks.

## Acceptance

- Migration round trip passes.
- Fixtures cover every category.
- Constraints prevent duplicate and cross-workspace mistakes.
