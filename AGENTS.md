# HandoffProof agent instructions

This repository builds a portfolio-grade SaaS that verifies whether lead handoffs reached their required destination state.

## Before changing anything

1. Read `docs/STATUS.md`.
2. Read `docs/PLAN.md` and the single active file in `tasks/`.
3. Read the relevant contract: `docs/API.md`, `docs/DATABASE.md`, or `docs/ARCHITECTURE.md`.
4. Inspect implementation and tests. Code, schemas, migrations, configuration, and tests are authoritative.
5. Work on one unchecked task at a time.

## Product boundary

- First workflow: compare source CSV submissions with destination CSV contacts.
- First live integration later: Typeform to HubSpot.
- MVP is read-only. Never edit CRM data, resend messages, merge contacts, or retry external actions.
- Each result is `matched`, `missing`, `duplicate`, `field_mismatch`, `excluded`, or `unknown`.
- Missing coverage or connector failure produces `unknown`, never a false healthy result.
- Core matching is deterministic. AI may suggest mappings or summarize evidence only after the core works.

## Engineering rules

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, pytest.
- Frontend: React, TypeScript, Vite, Vitest, React Testing Library.
- Celery and Redis are added only after synchronous reconciliation works.
- Validate external input at the API boundary.
- Store timestamps in UTC; expose ISO 8601 values.
- Scope every business-data query and row by `workspace_id`.
- Never commit secrets, tokens, customer exports, or production payloads.
- Do not claim completion until the active task's acceptance checks pass.

## Required handoff

1. Check off only verified work in the active task.
2. Update `docs/STATUS.md`: completed work, checks run, blockers, and exactly three next actions.
3. Add a decision to `docs/DECISIONS.md` only when it materially changes the project.
4. Update API/database/architecture docs only when that implementation changes.
5. Report changed files, checks, failures, and remaining risk.
6. When a phase finishes, add its simple explanation, technical flow, examples,
   concepts, and self-study search terms to `docs/LEARNING_GUIDE.md`.

## Forbidden shortcuts

- Placeholder files are not implemented features.
- Never invent test or customer results.
- Never replace deterministic reconciliation with LLM judgment.
- Do not start live connectors before Task 04 passes with fixtures.
- Do not create duplicate plan, state, or decision documents.
