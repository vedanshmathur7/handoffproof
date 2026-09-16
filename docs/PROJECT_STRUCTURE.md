# Project structure

```text
AGENTS.md                  instructions for every coding agent
README.md                  human entry point
docs/                      product and engineering contracts
docs/DOCUMENTATION_MAP.md  documentation hierarchy and ownership
tasks/                     ordered implementation checklists
research/                  market research and decision report
Makefile                   shared setup, run, and verification commands
compose.yaml               local PostgreSQL service and durable volume
backend/pyproject.toml      Python dependencies and tool configuration
backend/app/models.py       PostgreSQL ORM entities and invariants
backend/app/api/           FastAPI routes
backend/app/domain/        deterministic business logic
backend/app/services/      use-case coordination
backend/app/repositories/  persistence adapters
backend/app/connectors/    external read-only connectors
backend/app/workers/       scheduled/background tasks
backend/tests/             backend tests and fixtures
backend/migrations/        versioned PostgreSQL schema changes
frontend/src/api/          HTTP client
frontend/src/features/     feature screens and components
frontend/src/types/        shared TypeScript types
frontend/tests/            frontend behavior tests
frontend/package.json      Node dependencies and scripts
```

Do not add a second location for plans, status, decisions, API contracts, or database contracts. Placeholder files do not prove that a feature exists.
