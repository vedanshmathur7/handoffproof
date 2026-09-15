# Documentation map

## Hierarchy

1. Running code, configuration, migrations, and tests are authoritative for implemented behavior.
2. `docs/REQUIREMENTS.md`, `docs/API.md`, and `docs/DATABASE.md` are contracts; unresolved differences are defects.
3. `docs/STATUS.md` is the only current-state record.
4. `docs/PLAN.md` owns phase order; `tasks/` owns exact work checklists.
5. Context, architecture, decisions, and troubleshooting explain why and how.
6. Market research supports product selection but does not define application behavior.

## File ownership

| File | Reader and purpose | Include | Exclude | Source and updater | Authority / update trigger |
| --- | --- | --- | --- | --- | --- |
| `README.md` | Interviewer/new developer entry point | Problem, demo, verified setup | Detailed state or every task | Summarizes code and core docs; task owner updates | Descriptive; release/setup change |
| `AGENTS.md` | Every AI/developer | Workflow, guardrails, source-of-truth rules | Feature diary | Maintainers | Authoritative repository instruction; convention change |
| `docs/PROJECT_CONTEXT.md` | Product/development newcomer | User, job, scope, success | Technical implementation detail | Requirements and decisions; product owner | Descriptive; product boundary change |
| `docs/REQUIREMENTS.md` | Builder/tester | Stable behavior and quality requirements | Current progress | Approved product behavior; task owner | Contract; behavior change |
| `docs/ARCHITECTURE.md` | Developer/agent | Components, boundaries, data flow, trust rules | Every class/function | Running implementation and ADRs; architecture task owner | Descriptive until built, then contract-level; boundary change |
| `docs/PROJECT_STRUCTURE.md` | New developer/agent | Important directories and responsibilities | File-by-file inventory | Repository structure; task owner | Descriptive; major directory change |
| `docs/DEVELOPMENT_GUIDE.md` | Local developer | Verified setup and commands | Guessed commands | Executed project configuration; task owner | Descriptive; tool/command change |
| `docs/API.md` | Frontend/backend developer | Implemented endpoint contract and examples | Business rationale | OpenAPI and tests; API task owner | Contract; route/schema change |
| `docs/DATABASE.md` | Backend developer | Entities, relationships, invariants | Migration SQL copies | Migrations and model tests; schema task owner | Contract summary; migration/invariant change |
| `docs/DECISIONS.md` | Future maintainer | Consequential problem/options/decision/tradeoffs | Trivial edits or status | Approved ADRs; decision maker | Historical authoritative rationale; consequential decision |
| `docs/TROUBLESHOOTING.md` | Developer/operator | Reproduced symptoms and verified fixes | Guesses | Incident evidence; person verifying fix | Descriptive; recurring verified issue |
| `docs/LEARNING_GUIDE.md` | Project owner/learner | Simple examples, technical flow, concepts, and search terms for completed phases | Current status and task checklists | Verified implementation; phase owner | Descriptive; phase completion |
| `docs/PLAN.md` | Planner/agent | Phase order and exit conditions | Checkbox details | Requirements and approved sequence; maintainer | Authoritative plan; sequence/scope change |
| `docs/STATUS.md` | Every session | Verified completion, current work, blockers, checks, next three actions | Diary or unverified percent | Actual repository/check output; active task owner | Authoritative current state; every meaningful task |
| `tasks/*.md` | Implementing agent | Atomic steps and acceptance conditions | Cross-project narrative | Plan and contracts; task owner | Authoritative task checklist; task refinement/completion |
| `research/` | Founder/reviewer | Evidence and market decision | Application truth | Cited research; researcher | Historical evidence; research refresh |

## Files deliberately not created

- `.ai/AGENTS.md`: duplicates the discoverable root `AGENTS.md`.
- `.ai/CURRENT_STATE.md`: duplicates `docs/STATUS.md`.
- `.ai/TODO.md`: duplicates ordered `tasks/*.md`.
- `.ai/CHANGELOG.md`: Git history plus status and ADRs are sufficient before a release exists.
- Separate phase files: `docs/PLAN.md` already owns phase definitions.
- Generated API/database reference: create it from code only after implementation exists.

## Synchronization rule

Change the source first, run checks, then update only documents affected by the verified change. If documentation and implementation disagree, do not copy the disagreement elsewhere: correct the owning contract or implementation and record unresolved conflict as a blocker.

## Multi-agent workflow

1. One coordinator owns `docs/STATUS.md` and selects the active task.
2. Each agent reads the same entry documents before work.
3. Parallel work is allowed only when file ownership does not overlap and prerequisite tasks are complete.
4. Each agent reports files, checks, failures, and contract effects.
5. The coordinator integrates results, reruns shared checks, updates status once, and selects the next task.
6. Hidden chat context is never the only place containing a decision or blocker.
