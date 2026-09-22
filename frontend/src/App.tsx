import { useEffect, useRef, useState } from "react";

import {
  addReview,
  createRun,
  createWorkspace,
  exportUrl,
  getResults,
} from "./api/client";
import { ImportWizard } from "./features/imports/ImportWizard";
import { EvidenceDetail } from "./features/reconciliations/EvidenceDetail";
import { ExceptionList } from "./features/reconciliations/ExceptionList";
import { Summary } from "./features/reconciliations/Summary";
import type {
  Category,
  ImportResult,
  ReconciliationResult,
  RuleResult,
  RunSummary,
  Workspace,
} from "./types/reconciliation";

function newIdempotencyKey() {
  return globalThis.crypto?.randomUUID?.() ?? `run-${Date.now()}`;
}

function App() {
  const bootstrapStarted = useRef(false);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [source, setSource] = useState<ImportResult | null>(null);
  const [destination, setDestination] = useState<ImportResult | null>(null);
  const [rule, setRule] = useState<RuleResult | null>(null);
  const [run, setRun] = useState<RunSummary | null>(null);
  const [results, setResults] = useState<ReconciliationResult[]>([]);
  const [selected, setSelected] = useState<ReconciliationResult | null>(null);
  const [filter, setFilter] = useState<Category | undefined>();
  const [runLoading, setRunLoading] = useState(false);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [error, setError] = useState("");

  async function bootstrapWorkspace() {
    setWorkspaceLoading(true);
    setError("");
    try {
      setWorkspace(await createWorkspace());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not create the local demo workspace.",
      );
    } finally {
      setWorkspaceLoading(false);
    }
  }

  useEffect(() => {
    if (bootstrapStarted.current) return;
    bootstrapStarted.current = true;
    void bootstrapWorkspace();
  }, []);

  function handleReady(
    sourceImport: ImportResult,
    destinationImport: ImportResult,
    savedRule: RuleResult,
  ) {
    setSource(sourceImport);
    setDestination(destinationImport);
    setRule(savedRule);
    setRun(null);
    setResults([]);
    setSelected(null);
  }

  async function loadResults(
    currentRun: RunSummary,
    currentFilter?: Category,
  ) {
    if (!workspace) return;
    setResultsLoading(true);
    try {
      const page = await getResults(workspace.id, currentRun.id, currentFilter);
      setResults(page.items);
      setSelected((current) =>
        page.items.find((item) => item.id === current?.id) ?? page.items[0] ?? null,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load results.");
    } finally {
      setResultsLoading(false);
    }
  }

  async function startRun() {
    if (!workspace || !source || !destination || !rule) return;
    setRunLoading(true);
    setError("");
    try {
      const created = await createRun(
        workspace.id,
        source.id,
        destination.id,
        rule.id,
        newIdempotencyKey(),
      );
      setRun(created);
      setFilter(undefined);
      await loadResults(created);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Reconciliation could not run.",
      );
    } finally {
      setRunLoading(false);
    }
  }

  async function changeFilter(category?: Category) {
    if (!run) return;
    setFilter(category);
    await loadResults(run, category);
  }

  async function submitReview(
    resultId: string,
    reviewer: string,
    annotation: string,
  ) {
    if (!workspace || !run) return;
    setReviewBusy(true);
    setError("");
    try {
      const review = await addReview(
        workspace.id,
        resultId,
        reviewer,
        annotation,
      );
      setResults((current) =>
        current.map((item) =>
          item.id === resultId
            ? { ...item, reviews: [...item.reviews, review] }
            : item,
        ),
      );
      setSelected((current) =>
        current?.id === resultId
          ? { ...current, reviews: [...current.reviews, review] }
          : current,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save review.");
    } finally {
      setReviewBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Workflow evidence, without guesswork</p>
          <h1>HandoffProof</h1>
          <p className="intro">
            Prove whether every lead reached the destination—then inspect the exact
            evidence behind every exception.
          </p>
        </div>
        <div className="trust-card">
          <span className="trust-icon">HP</span>
          <div>
            <strong>Read-only by design</strong>
            <p>No CRM edits. No retries. No AI guesses.</p>
          </div>
        </div>
      </header>

      <nav className="progress-strip" aria-label="Workflow progress">
        <span className={workspace ? "done" : "active"}>Workspace</span>
        <span className={source && destination ? "done" : workspace ? "active" : ""}>
          Imports
        </span>
        <span className={rule ? "done" : source && destination ? "active" : ""}>
          Rule
        </span>
        <span className={run ? "done" : rule ? "active" : ""}>Evidence</span>
      </nav>

      {error && (
        <div className="error-banner" role="alert">
          <div>
            <strong>Something needs attention</strong>
            <p>{error}</p>
          </div>
          <button type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}

      {workspaceLoading ? (
        <section className="bootstrap-card" aria-live="polite">
          <span className="spinner" />
          <div>
            <h2>Preparing a private demo workspace…</h2>
            <p>Creating an isolated place for this browser session.</p>
          </div>
        </section>
      ) : !workspace ? (
        <section className="bootstrap-card">
          <div>
            <h2>Demo workspace unavailable</h2>
            <p>Start the API and database, then retry.</p>
          </div>
          <button
            className="button primary-button"
            type="button"
            onClick={() => void bootstrapWorkspace()}
          >
            Retry workspace setup
          </button>
        </section>
      ) : (
        <>
          <div className="workspace-chip">
            <span className="status-dot" />
            Workspace ready
            <code>{workspace.id.slice(0, 8)}</code>
          </div>
          <ImportWizard
            workspaceId={workspace.id}
            onReady={handleReady}
            onError={setError}
          />
        </>
      )}

      {workspace && source && destination && rule && !run && (
        <section className="launch-card">
          <div className="step-number">04</div>
          <div>
            <p className="section-kicker">Ready to compare</p>
            <h2>Run the evidence check</h2>
            <p>
              Version {rule.version} will classify every accepted source row exactly
              once. “Unknown” is used whenever the evidence is insufficient.
            </p>
          </div>
          <button
            className="button run-button"
            type="button"
            disabled={runLoading}
            onClick={() => void startRun()}
          >
            {runLoading ? "Reconciling records…" : "Run reconciliation →"}
          </button>
        </section>
      )}

      {run && (
        <>
          <Summary run={run} />
          <div className="result-actions">
            <p>Machine evidence is frozen. Reviews are append-only.</p>
            <a
              className="button secondary-button"
              href={exportUrl(run.workspace_id, run.id)}
              download
            >
              Download results CSV
            </a>
          </div>
          <div className="evidence-layout">
            <ExceptionList
              results={results}
              selectedId={selected?.id}
              filter={filter}
              loading={resultsLoading}
              onFilter={(category) => void changeFilter(category)}
              onSelect={setSelected}
            />
            <EvidenceDetail
              result={selected}
              reviewBusy={reviewBusy}
              onReview={submitReview}
            />
          </div>
        </>
      )}
    </main>
  );
}

export default App;
