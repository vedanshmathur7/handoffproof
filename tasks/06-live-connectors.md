# Task 06: Typeform and HubSpot shadow connectors

## Goal

Reuse the engine with one live, read-only handoff.

## Steps

- [ ] Confirm test accounts and least-privilege read scopes.
- [ ] Verify current official pagination, rate limits, indexing delay, retention, and token behavior.
- [ ] Define connector output using the same normalized contract as CSV.
- [ ] Implement Typeform polling with overlap and deduplication.
- [ ] Implement HubSpot reads with pagination and coverage watermarks.
- [ ] Encrypt credentials and exclude them from logs/responses.
- [ ] Map throttling, incomplete pages, stale watermarks, and failures to partial/failed coverage.
- [ ] Test pagination, retry bounds, throttling, malformed records, and expired credentials using mocks.
- [ ] Add scheduling only after manual reads pass.
- [ ] Prove connectors cannot write, merge, delete, or message.
- [ ] Compare consented test results with a manual audit.
- [ ] Update affected contracts and status.

## Acceptance

- Live reconciliation is read-only and coverage-aware.
- Provider failures never become false matches.
- Product and manual audit agree on adjudicated test cases.
