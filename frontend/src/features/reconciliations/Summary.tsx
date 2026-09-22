import type { Category, RunSummary } from "../../types/reconciliation";
import { categories } from "../../types/reconciliation";

interface SummaryProps {
  run: RunSummary;
}

const categoryLabels: Record<Category, string> = {
  matched: "Matched",
  missing: "Missing",
  duplicate: "Duplicate",
  field_mismatch: "Field mismatch",
  excluded: "Excluded",
  unknown: "Unknown",
};

export function Summary({ run }: SummaryProps) {
  const total = Object.values(run.result_counts).reduce(
    (sum, count) => sum + count,
    0,
  );
  return (
    <section className="summary-section" aria-labelledby="summary-title">
      <div className="summary-topline">
        <div>
          <p className="section-kicker">Reconciliation complete</p>
          <h2 id="summary-title">{total} source records classified</h2>
        </div>
        <span className={`coverage-pill coverage-${run.coverage}`}>
          {run.coverage} coverage
        </span>
      </div>
      {run.coverage !== "complete" && (
        <div className="coverage-warning" role="alert">
          <strong>Do not treat this run as healthy.</strong>
          <span>
            Destination coverage is {run.coverage}; insufficient evidence is reported
            as unknown.
          </span>
        </div>
      )}
      <div className="summary-grid">
        {categories.map((category) => (
          <article className={`metric metric-${category}`} key={category}>
            <strong>{run.result_counts[category] ?? 0}</strong>
            <span>{categoryLabels[category]}</span>
          </article>
        ))}
      </div>
      <p className="run-meta">
        Rule v{run.rule_version} · Completed {formatTimestamp(run.completed_at)}
      </p>
    </section>
  );
}

function formatTimestamp(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
