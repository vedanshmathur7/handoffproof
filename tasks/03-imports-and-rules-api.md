# Task 03: Imports and rules API

## Goal

Upload observations and create immutable reconciliation rules.

## Steps

- [x] Implement demo workspace creation.
- [x] Define CSV schemas from the fixtures.
- [x] Reject wrong type, oversized file, missing headers, invalid timestamps, and blank identities.
- [x] Preserve safe original evidence and normalize configured fields.
- [x] Report total, accepted, rejected, and duplicate-row counts.
- [x] Assign complete, partial, or failed coverage by explicit rules.
- [x] Implement source/destination upload and import-status endpoints.
- [x] Define rule input: eligibility, identity, required fields, wait window, timezone.
- [x] Validate selected fields against imported schemas.
- [x] Save every rule change as a new immutable version.
- [x] Generate API examples from OpenAPI and update `docs/API.md`.
- [x] Test success, invalid rows, partial coverage, invalid rules, idempotency, and isolation.
- [x] Run all checks and update status.

## Acceptance

- Both fixtures import with exact expected counts.
- Invalid input has a stable error code.
- Rule versions cannot be edited in place.

## Verified on 2026-09-22

- The checked-in source and destination fixtures imported with exact counts.
- Malformed rows produced all four manifest reason codes and failed coverage.
- Partial and duplicate-row inputs reported truthful coverage and counts.
- Repeat upload returned the same import; cross-workspace status access returned 404.
- Two rule changes created distinct versions 1 and 2; invalid fields were rejected.
- Migration `382806336a30` passed downgrade, upgrade, and schema-drift checks.
- `make check` passed 16 backend tests plus frontend tests, lint, types, and build.
