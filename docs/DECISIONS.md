# Architectural decisions

## ADR-001: Narrow lead handoff reconciliation

- Problem: Generic AI reliability is too broad for a small team and a clear demo.
- Options: exception manager, agent test platform, finance reconciliation, lead handoff verifier.
- Decision: Build a lead handoff verifier first.
- Reason: It has a visible end-to-end result and safe fixture-based demo.
- Tradeoff: It cannot judge semantic output quality.
- Consequence: Unrelated features require a new decision.

## ADR-002: CSV proof before live APIs

- Problem: OAuth and provider limits can delay proof of core value.
- Options: live integrations first; CSV proof first.
- Decision: Build CSV imports first and reuse the domain engine for connectors.
- Reason: It makes matching reproducible and interview-friendly.
- Tradeoff: Early product is not continuously monitoring.
- Consequence: Live connectors wait until Task 04 passes.

## ADR-003: Deterministic and read-only core

- Problem: Reliability cannot depend on another non-deterministic judgment.
- Options: LLM classification; deterministic rules; hybrid core.
- Decision: Core categories use deterministic rules; MVP never mutates external systems.
- Reason: Results must be reproducible and explainable.
- Tradeoff: Ambiguous cases remain `unknown`.
- Consequence: AI is optional assistance, never source of truth.
