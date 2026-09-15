# Requirements

## Functional requirements

- FR-01: Create a demo workspace.
- FR-02: Import a source CSV and display accepted and rejected row counts.
- FR-03: Import a destination CSV and display accepted and rejected row counts.
- FR-04: Configure a deterministic identity key and required fields.
- FR-05: Run reconciliation for selected source and destination imports.
- FR-06: Give every eligible source record exactly one result category.
- FR-07: Include evidence, rule version, and reason code in every result.
- FR-08: Filter, review, annotate, and export exceptions.
- FR-09: Return `unknown` when coverage is insufficient.
- FR-10: Include seeded demo examples for every category.

## Result categories

- `matched`: exactly one destination record satisfies the rule.
- `missing`: the waiting window passed and no candidate exists.
- `duplicate`: multiple destination records match the identity.
- `field_mismatch`: one candidate exists but a required field differs or is absent.
- `excluded`: an explicit rule says the source record should not transfer.
- `unknown`: trustworthy data is insufficient for a decision.

## Non-functional requirements

- NFR-01: External systems remain read-only.
- NFR-02: Re-running the same reconciliation is idempotent.
- NFR-03: Business data is workspace-scoped.
- NFR-04: Invalid rows receive reasons and are never silently dropped.
- NFR-05: Core matching works without an LLM or network.
- NFR-06: Fixtures and automated tests make results reproducible.
- NFR-07: Logs exclude tokens and full private payloads.
- NFR-08: UI covers loading, empty, partial, success, and error states.

## Acceptance scenario

Checked-in sample imports must produce every result category. Exact IDs, counts, and reason codes will be frozen in the Task 02 fixture manifest.
