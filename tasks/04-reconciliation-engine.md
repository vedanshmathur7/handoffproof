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

- [ ] Implement typed normalization as pure functions.
- [ ] Implement each branch as pure domain logic with stable reason codes.
- [ ] Add table-driven tests from the fixture manifest.
- [ ] Test invariants: one result per eligible source; no healthy claim under incomplete coverage.
- [ ] Implement service and transaction boundary.
- [ ] Add idempotent run creation and concurrent-request test.
- [ ] Store candidates and field-level evidence.
- [ ] Implement summary, filtered/paginated results, reviews, and export.
- [ ] Run the full sample through API integration tests.
- [ ] Verify exact fixture counts and update contracts.

## Acceptance

- Manifest passes without network or LLM.
- Repeated requests do not duplicate data.
- Every result exposes its rule and evidence.
