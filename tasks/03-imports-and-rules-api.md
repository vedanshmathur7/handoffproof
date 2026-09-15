# Task 03: Imports and rules API

## Goal

Upload observations and create immutable reconciliation rules.

## Steps

- [ ] Implement demo workspace creation.
- [ ] Define CSV schemas from the fixtures.
- [ ] Reject wrong type, oversized file, missing headers, invalid timestamps, and blank identities.
- [ ] Preserve safe original evidence and normalize configured fields.
- [ ] Report total, accepted, rejected, and duplicate-row counts.
- [ ] Assign complete, partial, or failed coverage by explicit rules.
- [ ] Implement source/destination upload and import-status endpoints.
- [ ] Define rule input: eligibility, identity, required fields, wait window, timezone.
- [ ] Validate selected fields against imported schemas.
- [ ] Save every rule change as a new immutable version.
- [ ] Generate API examples from OpenAPI and update `docs/API.md`.
- [ ] Test success, invalid rows, partial coverage, invalid rules, idempotency, and isolation.
- [ ] Run all checks and update status.

## Acceptance

- Both fixtures import with exact expected counts.
- Invalid input has a stable error code.
- Rule versions cannot be edited in place.
