import { useState } from "react";

import type { ReconciliationResult } from "../../types/reconciliation";

interface EvidenceDetailProps {
  result: ReconciliationResult | null;
  reviewBusy: boolean;
  onReview: (resultId: string, reviewer: string, annotation: string) => Promise<void>;
}

function label(value: string) {
  return value.replaceAll("_", " ");
}

function EvidenceTable({ data }: { data: Record<string, unknown> }) {
  return (
    <dl className="evidence-table">
      {Object.entries(data).map(([key, value]) => (
        <div key={key}>
          <dt>{label(key)}</dt>
          <dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export function EvidenceDetail({
  result,
  reviewBusy,
  onReview,
}: EvidenceDetailProps) {
  const [reviewer, setReviewer] = useState("reviewer@example.test");
  const [annotation, setAnnotation] = useState("");

  if (!result) {
    return (
      <aside className="evidence-panel empty-evidence">
        <p>Select a result to inspect its evidence.</p>
      </aside>
    );
  }

  async function submitReview(event: React.FormEvent) {
    event.preventDefault();
    if (!result || !annotation.trim()) return;
    await onReview(result.id, reviewer, annotation);
    setAnnotation("");
  }

  const differences = Array.isArray(result.evidence.differences)
    ? result.evidence.differences
    : [];

  return (
    <aside className="evidence-panel" aria-labelledby="evidence-title">
      <div className="evidence-header">
        <div>
          <p className="section-kicker">Decision evidence</p>
          <h2 id="evidence-title">{result.source_record_id}</h2>
        </div>
        <span className={`category-tag category-${result.category}`}>
          {label(result.category)}
        </span>
      </div>
      <div className="reason-box">
        <span>Machine reason</span>
        <strong>{result.reason_code}</strong>
        <p>This reason remains unchanged when reviewers add notes.</p>
      </div>

      <details open>
        <summary>Source evidence</summary>
        <EvidenceTable data={result.source_evidence} />
      </details>

      {differences.length > 0 && (
        <details open>
          <summary>Field differences</summary>
          <pre>{JSON.stringify(differences, null, 2)}</pre>
        </details>
      )}

      <details open={result.candidates.length > 0}>
        <summary>Destination candidates ({result.candidates.length})</summary>
        {result.candidates.length === 0 ? (
          <p className="muted">No destination candidate matched the identity.</p>
        ) : (
          result.candidates.map((candidate) => (
            <article className="candidate-card" key={candidate.destination_observation_id}>
              <strong>
                #{candidate.rank} · {candidate.external_record_id}
              </strong>
              <EvidenceTable data={candidate.original_evidence} />
            </article>
          ))
        )}
      </details>

      <div className="rule-proof">
        <span>Applied rule</span>
        <strong>
          {result.rule.name} · version {result.rule.version}
        </strong>
        <p>
          Identity: {result.rule.identity_field} · Required: {result.rule.required_fields.join(", ")} · Wait: {result.rule.wait_seconds}s · {result.rule.timezone}
        </p>
      </div>

      <section className="review-section">
        <h3>Reviewer notes</h3>
        {result.reviews.length === 0 ? (
          <p className="muted">No notes yet.</p>
        ) : (
          <ul className="review-list">
            {result.reviews.map((review) => (
              <li key={review.id}>
                <strong>{review.reviewer}</strong>
                <p>{review.annotation}</p>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={(event) => void submitReview(event)}>
          <label className="field">
            <span>Reviewer</span>
            <input
              aria-label="Reviewer"
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Note</span>
            <textarea
              aria-label="Review note"
              value={annotation}
              onChange={(event) => setAnnotation(event.target.value)}
              placeholder="Add context without changing the machine result…"
            />
          </label>
          <button
            className="button secondary-button"
            disabled={!annotation.trim() || reviewBusy}
            type="submit"
          >
            {reviewBusy ? "Saving note…" : "Add review note"}
          </button>
        </form>
      </section>
    </aside>
  );
}
