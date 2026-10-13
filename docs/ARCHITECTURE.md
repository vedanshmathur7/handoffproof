# Architecture

## Runtime

```text
React UI -> FastAPI -> application services -> PostgreSQL
                 \-> deterministic reconciliation engine
Later: scheduler -> worker -> read-only Typeform/HubSpot connectors
```

FastAPI, React, and PostgreSQL are runnable. The workspace, CSV import, validation,
normalization, evidence, immutable-rule flow, deterministic reconciliation,
reviews, export, and the complete reviewer dashboard are implemented. Task 06 now
has read-only Typeform and HubSpot client libraries; credential wiring, persisted
checkpoints, and a consented live manual audit remain unfinished.

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
5. Classify every accepted source observation exactly once, including explicit
   `excluded` and evidence-limited `unknown` outcomes.
6. Save results, ranked candidates, field differences, and counts in one transaction.
7. Serve paginated/filterable results, append-only reviews, and safe CSV export.

## Trust rules

- Import coverage is `complete`, `partial`, or `failed`.
- Partial or failed coverage cannot yield an overall healthy result.
- Original evidence is immutable; normalization and rules are versioned.
- Human reviews never overwrite the machine reason.
- Connector records are normalized through the existing import contract before a
  reconciliation run; connectors never classify a result themselves.
- A failed first provider page produces failed coverage; a later page failure or
  throttling produces partial coverage. Both states block healthy conclusions.
- Connector clients expose GET requests only. Their tokens are passed only in an
  Authorization header and are never included in snapshots, errors, or logs.

## Later background work

Celery and Redis are planned for scheduled reads. PostgreSQL remains the durable record of jobs, watermarks, observations, and results.
