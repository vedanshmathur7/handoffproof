# Project context

## Purpose

HandoffProof proves whether a business handoff produced the expected destination records. It starts as an interview portfolio project and a testable SaaS hypothesis.

## Initial user

An automation or RevOps operator responsible for several lead workflows who currently checks logs or compares exports after a reported problem.

## Initial workflow

1. Import source lead submissions from CSV.
2. Import destination CRM contacts from CSV.
3. Define eligibility, identity, required-field, and waiting-window rules.
4. Compare the datasets.
5. Show evidence-backed results in an exception queue.
6. Export results for review or repair outside HandoffProof.

## Portfolio success

A reviewer can run the project locally, import sample files, execute reconciliation, inspect every result category, and understand why each result occurred.

## Out of scope for MVP

- Automatic CRM writes or record repair
- Sending messages or retrying external workflows
- Universal workflow rollback
- Generic AI-agent observability
- Billing, enterprise SSO, or many integrations

## Source of truth

Requirements define intent. Code, migrations, configuration, and passing tests confirm implementation. `docs/STATUS.md` records what is verified now.
