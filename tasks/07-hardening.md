# Task 07: Hardening

## Goal

Make demonstrated behavior safe, observable, repeatable, and maintainable.

## Steps

- [ ] Add deployment-appropriate authentication or restrict demo access explicitly.
- [ ] Verify isolation across API, service, repository, and export boundaries.
- [ ] Protect against oversized files, wrong content, formula injection, and malicious headers.
- [ ] Add request IDs and structured, redacted logs.
- [ ] Document and perform one database backup/restore.
- [ ] Add connector timeouts, bounded retries, and circuit behavior.
- [ ] Add durable job records before queue workers.
- [ ] Add an independent stale-job and coverage watchdog.
- [ ] Load test agreed demo volume and record dataset, machine, and latency.
- [ ] Run dependency, static, unit, integration, UI, and build checks.
- [ ] Fix release blockers or record them honestly.

## Acceptance

- No tested path leaks workspace data.
- Dependency failure visibly degrades coverage.
- Restore and full verification pass.
