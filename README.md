# HandoffProof

HandoffProof is a read-only workflow reliability dashboard. It compares source records, such as lead-form submissions, with the records that should exist in a destination such as HubSpot. It shows missing records, duplicates, wrong required fields, intentional exclusions, and cases it cannot safely judge.

Example: a form accepted 100 submissions. HandoffProof verifies which eligible submissions reached the CRM and attaches source and destination evidence to every exception.

## Current repository state

The runnable foundation and versioned PostgreSQL schema exist. Health checks,
workspace isolation, deterministic CSV fixtures, tests, linting, type checking, and
production frontend builds are verified. CSV import APIs and reconciliation behavior
have not been implemented. Start with
[docs/STATUS.md](docs/STATUS.md), then follow [docs/PLAN.md](docs/PLAN.md).

## Stack

- FastAPI and PostgreSQL backend
- React and TypeScript frontend
- CSV demo before live Typeform and HubSpot integrations
- Celery and Redis only when background execution becomes necessary

Run `make setup`, `make deps-up`, and `make check` from the repository root. The
full verified workflow is in [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md).

Every GitHub push and pull request runs the same backend and frontend checks through
`.github/workflows/ci.yml`.
