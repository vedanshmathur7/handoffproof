import type {
  Category,
  ReconciliationResult,
} from "../../types/reconciliation";
import { categories } from "../../types/reconciliation";

interface ExceptionListProps {
  results: ReconciliationResult[];
  selectedId?: string;
  filter?: Category;
  loading: boolean;
  onFilter: (category?: Category) => void;
  onSelect: (result: ReconciliationResult) => void;
}

const label = (value: string) => value.replaceAll("_", " ");

export function ExceptionList({
  results,
  selectedId,
  filter,
  loading,
  onFilter,
  onSelect,
}: ExceptionListProps) {
  return (
    <section className="results-panel" aria-labelledby="results-title">
      <div className="results-heading">
        <div>
          <p className="section-kicker">Result explorer</p>
          <h2 id="results-title">Inspect every decision</h2>
        </div>
        <span>{results.length} shown</span>
      </div>
      <div className="filter-row" aria-label="Result category filters">
        <button
          className={!filter ? "active" : ""}
          type="button"
          onClick={() => onFilter(undefined)}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            className={filter === category ? "active" : ""}
            key={category}
            type="button"
            onClick={() => onFilter(category)}
          >
            {label(category)}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="list-state">Loading filtered results…</div>
      ) : results.length === 0 ? (
        <div className="list-state">No results in this category.</div>
      ) : (
        <div className="result-list">
          {results.map((result) => (
            <button
              className={`result-row ${
                selectedId === result.id ? "is-selected" : ""
              }`}
              key={result.id}
              type="button"
              onClick={() => onSelect(result)}
            >
              <span className={`category-dot category-${result.category}`} />
              <span className="result-copy">
                <strong>{result.source_record_id}</strong>
                <small>{label(result.reason_code)}</small>
              </span>
              <span className={`category-tag category-${result.category}`}>
                {label(result.category)}
              </span>
              <span aria-hidden="true">→</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
