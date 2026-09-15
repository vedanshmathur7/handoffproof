# Implementation plan

## Execution rule

Work in task-number order. Open one task at a time. Perform checkboxes top to bottom. Run the check written for the step. If it fails, fix it before continuing. Never infer a later feature works because an earlier test passed.

## Phases

| Phase | Tasks | Exit condition |
| --- | --- | --- |
| Define | 00 | Scope, requirements, architecture, state, and tasks agree. |
| Foundation | 01 | Backend, frontend, database, and commands run locally. |
| Data | 02 | Versioned schema and deterministic fixtures exist. |
| Backend | 03–04 | Imports, rules, reconciliation, evidence, and exports pass. |
| Frontend | 05 | Reviewer completes the CSV workflow through the UI. |
| Live integration | 06 | Typeform-to-HubSpot shadow reconciliation works. |
| Harden | 07 | Security, observability, recovery, and full checks pass. |
| Release | 08 | Deployed demo works twice from a clean reset. |

Detailed instructions are in `tasks/00-documentation-baseline.md` through `tasks/08-portfolio-release.md`. This file owns phase order; task files own their exact checklists.
