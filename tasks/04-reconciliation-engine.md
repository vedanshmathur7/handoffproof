# Task 04: Reconciliation engine

## Goal

Produce one deterministic, explainable result per eligible source observation.

## Classification order

1. Untrustworthy coverage -> `unknown`.
2. Explicitly ineligible -> `excluded`.
3. Waiting window still open -> `unknown`.
4. Normalize configured identity.
5. Missing or ambiguous identity -> `unknown`.
6. Find destination candidates in scope.
7. Zero candidates -> `missing`.
8. Multiple candidates -> `duplicate`.
9. Compare required fields on one candidate.
10. Any difference -> `field_mismatch`.
11. Otherwise -> `matched`.

## Steps

- [x] Implement typed normalization as pure functions.
- [x] Implement each branch as pure domain logic with stable reason codes.
- [x] Add table-driven tests from the fixture manifest.
- [x] Test invariants: one result per eligible source; no healthy claim under incomplete coverage.
- [x] Implement service and transaction boundary.
- [x] Add idempotent run creation and concurrent-request test.
- [x] Store candidates and field-level evidence.
- [x] Implement summary, filtered/paginated results, reviews, and export.
- [x] Run the full sample through API integration tests.
- [x] Verify exact fixture counts and update contracts.

## Acceptance

- Manifest passes without network or LLM.
- Repeated requests do not duplicate data.
- Every result exposes its rule and evidence.

## Verified on 2026-09-22

- All six manifest cases passed pure table-driven tests without network or LLM.
- Complete fixtures produced 6 results: 1 matched, 2 missing, 1 duplicate,
  1 field mismatch, 1 excluded, and 0 unknown at the fixed evaluation time.
- Partial destination coverage produced 6 unknown results and no healthy result.
- Two concurrent requests with one idempotency key created one run and six results.
- Filters, pagination, candidate evidence, field differences, reviews, isolation, and
  CSV export passed API integration tests.
- All 28 backend tests, Ruff, mypy, and Alembic drift checks passed.
