# Task 05: Dashboard

## Goal

Let an interviewer complete the CSV workflow without API tools.

## Steps

- [x] Add local demo workspace bootstrap.
- [x] Build separate source and destination upload steps.
- [x] Show file schema, accepted/rejected counts, and row errors.
- [x] Build rule form from backend-returned fields.
- [x] Explain identity, eligibility, required fields, waiting, and unknown simply.
- [x] Start reconciliation and show truthful progress.
- [x] Display summary counts and coverage prominently.
- [x] Add exception filters for all categories.
- [x] Show source evidence, candidates, differences, rule version, and timestamps.
- [x] Add review notes without replacing machine reasons.
- [x] Add results download.
- [x] Handle loading, empty, partial, validation, server-error, and retry states.
- [x] Test these behaviors.
- [x] Run the entire workflow in a browser and record observed counts.

## Acceptance

- Fresh reviewer reaches results without code knowledge.
- Each exception is explainable from visible evidence.
- Partial coverage cannot look healthy.

## Verified on 2026-09-22

- Five frontend tests passed the workspace bootstrap/retry, guided CSV-to-results
  workflow, evidence, review, empty state, and partial-coverage warning.
- ESLint, TypeScript, and the Vite production build passed.
- A fresh Chrome session used the checked-in sample buttons and completed the whole
  workflow without API tools.
- Browser-observed imports: source 6 accepted/0 rejected; destination 4 accepted/0
  rejected; both reported complete coverage.
- Browser-observed results: 1 matched, 2 missing, 1 duplicate, 1 field mismatch,
  1 excluded, and 0 unknown.
- Duplicate evidence showed two ranked candidates. Mismatch evidence showed
  `company: correct company -> wrong company`, rule version 1, and the destination
  row. An appended review appeared without changing `REQUIRED_FIELD_MISMATCH`.
