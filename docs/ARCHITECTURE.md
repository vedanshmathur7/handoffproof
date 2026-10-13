# Architecture

## Runtime

```text
React UI -> FastAPI -> application services -> PostgreSQL
                 \-> deterministic reconciliation engine
Later: scheduler -> worker -> read-only Typeform/HubSpot connectors
```

FastAPI, React, and PostgreSQL are runnable. The workspace, CSV import, validation,
normalization, evidence, immutable-rule flow, deterministic reconciliation,
reviews, export, and the complete reviewer dashboard are implemented. Task 06 now
has read-only Typeform and HubSpot client libraries; credential wiring, persisted
checkpoints, and a consented live manual audit remain unfinished.

## Boundaries

- `api`: validates HTTP requests and returns response models.
- `services`: coordinates imports, rules, runs, and reviews.
- `domain`: contains pure reconciliation logic.
- `repositories`: handles persistence without classification logic.
- `connectors`: retrieves external data read-only after CSV proof.
- `workers`: runs scheduled work after synchronous flow works.
- `frontend`: displays backend truth and never recomputes categories.

## Data flow

1. Parse an import into normalized observations while preserving evidence.
2. Save metadata and observations in a workspace.
3. Freeze a versioned reconciliation rule.
4. Create a run referencing two completed imports and one rule.
5. Classify every accepted source observation exactly once, including explicit
   `excluded` and evidence-limited `unknown` outcomes.
6. Save results, ranked candidates, field differences, and counts in one transaction.
7. Serve paginated/filterable results, append-only reviews, and safe CSV export.

## Trust rules

- Import coverage is `complete`, `partial`, or `failed`.
- Partial or failed coverage cannot yield an overall healthy result.
- Original evidence is immutable; normalization and rules are versioned.
- Human reviews never overwrite the machine reason.
- Connector records are normalized through the existing import contract before a
  reconciliation run; connectors never classify a result themselves.
- A failed first provider page produces failed coverage; a later page failure or
  throttling produces partial coverage. Both states block healthy conclusions.
- Connector clients expose GET requests only. Their tokens are passed only in an
  Authorization header and are never included in snapshots, errors, or logs.
- Stored tokens are encrypted with Fernet keys from `CONNECTOR_ENCRYPTION_KEYS`
  (MultiFernet: the first key encrypts, every listed key decrypts, enabling key
  rotation). Without a valid key, credential operations fail closed with HTTP 503.

## Later background work

Celery and Redis are planned for scheduled reads. PostgreSQL remains the durable record of jobs, watermarks, observations, and results.

## Provider behavior (official docs checked 2026-10-13)

| Topic | Typeform Responses API | HubSpot CRM contacts (private app) |
| --- | --- | --- |
| Read endpoint | `GET /forms/{form_id}/responses` | `GET /crm/v3/objects/contacts` |
| Least-privilege scope | `responses:read` (`forms:read` only to list forms) | `crm.objects.contacts.read` |
| Pagination | `page_size` default 25, max 1000; `before` takes the last item's `token` (exclusive); `since`/`until` are inclusive ISO 8601 UTC to the second | `limit` max 100; `paging.next.after` is passed back as `after` |
| Rate limit | 2 requests/second per account | 100/10s per app (Free/Starter), 190/10s (Pro/Enterprise); daily limit shared per account; 429 for all calls once exceeded |
| Indexing delay | Responses from roughly the last 30 minutes may not be returned | List endpoint is not documented as delayed; Search is (and is capped at 5 req/s and 10,000 results), so it is not used |
| Retention | No automatic expiry; deleted responses and forms are permanently gone | Deleted contacts are archived, restorable for 90 days, and excluded from the default list |
| Tokens | Personal access token or OAuth token (`offline` scope for refresh) | Private app token, Bearer header; no fixed expiry, rotation expires the old token (immediately or after 7 days), rotation recommended every 6 months |

Implementation consequences:

- Clients space requests (Typeform 0.5 s, HubSpot 0.1 s) and wait for
  `Retry-After` or a capped backoff before their single bounded retry.
- The Typeform checkpoint never advances past `read time - 30 minutes`; the next
  read starts five minutes before that checkpoint and deduplicates by response ID.
- Expired, rotated, or revoked tokens surface as `CONNECTOR_AUTH_FAILED` and
  failed coverage.

Sources: typeform.com/developers (responses reference, walkthroughs, get-started,
scopes); developers.hubspot.com/docs (usage-details, crm/contacts, crm/search,
private-apps, delete-contact reference); Typeform help article 360040196472.
