# Task 00: Validate documentation

## Goal

Prove that a fresh agent can continue without hidden chat context.

## Steps

- [x] Read `AGENTS.md`, `docs/STATUS.md`, context, requirements, and architecture.
- [x] Confirm the MVP is read-only, CSV-first, deterministic, and limited to lead handoffs.
- [x] Confirm `docs/PLAN.md` names Tasks 00–08.
- [x] Confirm implementation placeholders in `docs/PROJECT_STRUCTURE.md` exist.
- [x] Search for contradictions about scope, stack, categories, and active task.
- [x] Fix each contradiction only in its owning document.
- [x] Run the acceptance commands below.
- [x] Record exact results in status.
- [x] Set completed tasks to 1/9 and active task to Task 01 only after all checks pass.
- [x] Replace status's next actions with the first three Task 01 actions.

## Acceptance commands

```bash
test -f AGENTS.md && test -f docs/STATUS.md && test -f docs/PLAN.md
find tasks -maxdepth 1 -type f -name '[0-9][0-9]-*.md' | sort
find backend frontend -type f | sort
rg -n 'generic AI reliability|automatic CRM writes|Active task:' AGENTS.md README.md docs tasks
```
