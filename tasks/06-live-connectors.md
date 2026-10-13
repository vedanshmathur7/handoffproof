# Task 06: Typeform and HubSpot shadow connectors

## Goal

Reuse the engine with one live, read-only handoff.

## Steps

- [ ] Confirm test accounts and least-privilege read scopes.
- [x] Verify current official pagination, rate limits, indexing delay, retention, and token behavior.
- [x] Define connector output using the same normalized contract as CSV.
- [x] Implement Typeform polling with overlap and deduplication.
- [x] Implement HubSpot reads with pagination and coverage watermarks.
- [x] Encrypt credentials and exclude them from logs/responses.
- [x] Map throttling, incomplete pages, stale watermarks, and failures to partial/failed coverage.
- [x] Test pagination, retry bounds, throttling, malformed records, and expired credentials using mocks.
- [ ] Add scheduling only after manual reads pass.
- [x] Prove connectors cannot write, merge, delete, or message.
- [ ] Compare consented test results with a manual audit.
- [x] Update affected contracts and status.

## Acceptance

- Live reconciliation is read-only and coverage-aware.
- Provider failures never become false matches.
- Product and manual audit agree on adjudicated test cases.
