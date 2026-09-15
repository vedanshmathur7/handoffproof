# Architecture

## Planned runtime

```text
React UI -> FastAPI -> application services -> PostgreSQL
                 \-> deterministic reconciliation engine
Later: scheduler -> worker -> read-only Typeform/HubSpot connectors
```

## Boundaries

- `api`: validates HTTP requests and returns response models.
- `services`: coordinates imports, rules, runs, and reviews.
- `domain`: contains pure reconciliation logic.
- `repositories`: handles persistence without classification logic.
- `connectors`: retrieves external data read-only after CSV proof.
- `workers`: runs scheduled work after synchronous flow works.
- `frontend`: displays backend truth and never recomputes categories.

## Data flow

1. Parse an import into normalized observations while preserving evidence.
2. Save metadata and observations in a workspace.
3. Freeze a versioned reconciliation rule.
4. Create a run referencing two completed imports and one rule.
5. Classify each eligible source observation exactly once.
6. Save results and counts in one transaction.
7. Serve the result to the UI and CSV export.

## Trust rules

- Import coverage is `complete`, `partial`, or `failed`.
- Partial or failed coverage cannot yield an overall healthy result.
- Original evidence is immutable; normalization and rules are versioned.
- Human reviews never overwrite the machine reason.

## Later background work

Celery and Redis are planned for scheduled reads. PostgreSQL remains the durable record of jobs, watermarks, observations, and results.
