import { useState } from "react";

import { createRule, uploadImport } from "../../api/client";
import { demoFile } from "../../demoFixtures";
import type {
  Coverage,
  ImportResult,
  RuleResult,
} from "../../types/reconciliation";

interface ImportWizardProps {
  workspaceId: string;
  onReady: (
    source: ImportResult,
    destination: ImportResult,
    rule: RuleResult,
  ) => void;
  onError: (message: string) => void;
}

interface UploadCardProps {
  kind: "source" | "destination";
  file: File | null;
  result: ImportResult | null;
  busy: boolean;
  coverage: Coverage;
  onFile: (file: File | null) => void;
  onCoverage: (coverage: Coverage) => void;
  onUpload: () => void;
}

const labels = {
  source: {
    step: "01",
    title: "Source submissions",
    description: "The records that should have reached the destination.",
  },
  destination: {
    step: "02",
    title: "Destination contacts",
    description: "The records that actually arrived in the receiving system.",
  },
};

function UploadCard({
  kind,
  file,
  result,
  busy,
  coverage,
  onFile,
  onCoverage,
  onUpload,
}: UploadCardProps) {
  const copy = labels[kind];
  return (
    <article className={`upload-card ${result ? "is-complete" : ""}`}>
      <div className="step-number">{copy.step}</div>
      <div className="upload-heading">
        <div>
          <p className="section-kicker">CSV import</p>
          <h3>{copy.title}</h3>
        </div>
        {result && <span className="done-badge">Imported</span>}
      </div>
      <p className="muted">{copy.description}</p>
      <label className="file-picker">
        <span>{file?.name ?? `Choose ${kind} CSV`}</span>
        <input
          aria-label={`Choose ${kind} CSV`}
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => onFile(event.target.files?.[0] ?? null)}
        />
      </label>
      <button
        className="sample-button"
        type="button"
        onClick={() => onFile(demoFile(kind))}
      >
        Use checked-in sample CSV
      </button>
      {kind === "destination" && (
        <label className="field compact-field">
          <span>Snapshot coverage</span>
          <select
            aria-label="Destination coverage"
            value={coverage}
            onChange={(event) => onCoverage(event.target.value as Coverage)}
          >
            <option value="complete">Complete snapshot</option>
            <option value="partial">Partial snapshot</option>
            <option value="failed">Failed snapshot</option>
          </select>
        </label>
      )}
      <button
        className="button secondary-button"
        type="button"
        disabled={!file || busy}
        onClick={onUpload}
      >
        {busy ? "Checking rows…" : result ? "Replace import" : "Validate & import"}
      </button>
      {result && (
        <div className="import-report" aria-label={`${kind} import report`}>
          <div>
            <strong>{result.accepted_rows}</strong>
            <span>accepted</span>
          </div>
          <div>
            <strong>{result.rejected_rows}</strong>
            <span>rejected</span>
          </div>
          <div>
            <strong>{result.duplicate_rows}</strong>
            <span>duplicates</span>
          </div>
          <p className={`coverage-label coverage-${result.coverage}`}>
            {result.coverage} coverage
          </p>
          <details>
            <summary>Detected schema ({result.schema_fields.length} fields)</summary>
            <code>{result.schema_fields.join(", ")}</code>
          </details>
          {result.row_errors.length > 0 && (
            <ul className="row-errors">
              {result.row_errors.map((error) => (
                <li key={`${error.row_number}-${error.code}`}>
                  Row {error.row_number}: {error.code}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </article>
  );
}

export function ImportWizard({
  workspaceId,
  onReady,
  onError,
}: ImportWizardProps) {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [destinationFile, setDestinationFile] = useState<File | null>(null);
  const [source, setSource] = useState<ImportResult | null>(null);
  const [destination, setDestination] = useState<ImportResult | null>(null);
  const [destinationCoverage, setDestinationCoverage] =
    useState<Coverage>("complete");
  const [busy, setBusy] = useState<string | null>(null);
  const [identityField, setIdentityField] = useState("email");
  const [eligibilityField, setEligibilityField] = useState("transfer_enabled");
  const [requiredFields, setRequiredFields] = useState<string[]>([
    "full_name",
    "company",
    "region",
  ]);
  const [waitSeconds, setWaitSeconds] = useState(300);
  const [timezone, setTimezone] = useState("UTC");

  const commonFields =
    source && destination
      ? source.schema_fields.filter((field) => destination.schema_fields.includes(field))
      : [];
  const comparableFields = commonFields.filter(
    (field) => !field.endsWith("_id") && !field.endsWith("_at"),
  );

  async function upload(kind: "source" | "destination") {
    const file = kind === "source" ? sourceFile : destinationFile;
    if (!file) return;
    setBusy(kind);
    onError("");
    try {
      const result = await uploadImport(
        workspaceId,
        kind,
        file,
        kind === "source" ? "complete" : destinationCoverage,
      );
      if (kind === "source") setSource(result);
      else setDestination(result);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Import failed.");
    } finally {
      setBusy(null);
    }
  }

  function toggleRequired(field: string) {
    setRequiredFields((current) =>
      current.includes(field)
        ? current.filter((item) => item !== field)
        : [...current, field],
    );
  }

  async function saveRule() {
    if (!source || !destination) return;
    setBusy("rule");
    onError("");
    try {
      const rule = await createRule({
        workspace_id: workspaceId,
        source_import_id: source.id,
        destination_import_id: destination.id,
        name: "Email lead handoff",
        eligibility: { field: eligibilityField, equals: "true" },
        identity_field: identityField,
        required_fields: requiredFields,
        wait_seconds: waitSeconds,
        timezone,
      });
      onReady(source, destination, rule);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Rule creation failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="workflow-section" aria-labelledby="imports-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Prepare the comparison</p>
          <h2 id="imports-title">Bring both sides of the handoff</h2>
        </div>
        <p>Files stay read-only. HandoffProof never edits either system.</p>
      </div>

      <div className="upload-grid">
        <UploadCard
          kind="source"
          file={sourceFile}
          result={source}
          busy={busy === "source"}
          coverage="complete"
          onFile={setSourceFile}
          onCoverage={() => undefined}
          onUpload={() => void upload("source")}
        />
        <UploadCard
          kind="destination"
          file={destinationFile}
          result={destination}
          busy={busy === "destination"}
          coverage={destinationCoverage}
          onFile={setDestinationFile}
          onCoverage={setDestinationCoverage}
          onUpload={() => void upload("destination")}
        />
      </div>

      {source && destination && (
        <article className="rule-card">
          <div className="step-number">03</div>
          <div className="rule-intro">
            <p className="section-kicker">Comparison rule</p>
            <h3>Define what “arrived correctly” means</h3>
            <p className="muted">
              Identity finds the same person. Eligibility decides which source rows
              should transfer. Required fields must agree. The wait window prevents
              calling a recent lead missing too early.
            </p>
          </div>
          <div className="rule-grid">
            <label className="field">
              <span>Identity field</span>
              <select
                aria-label="Identity field"
                value={identityField}
                onChange={(event) => setIdentityField(event.target.value)}
              >
                {commonFields.map((field) => (
                  <option key={field}>{field}</option>
                ))}
              </select>
              <small>Usually email: one normalized value links both systems.</small>
            </label>
            <label className="field">
              <span>Eligibility field</span>
              <select
                aria-label="Eligibility field"
                value={eligibilityField}
                onChange={(event) => setEligibilityField(event.target.value)}
              >
                {source.schema_fields.map((field) => (
                  <option key={field}>{field}</option>
                ))}
              </select>
              <small>Rows equal to “true” are expected to transfer.</small>
            </label>
            <label className="field">
              <span>Wait window (seconds)</span>
              <input
                aria-label="Wait window"
                type="number"
                min="0"
                value={waitSeconds}
                onChange={(event) => setWaitSeconds(Number(event.target.value))}
              />
              <small>Recent rows stay unknown until this time passes.</small>
            </label>
            <label className="field">
              <span>Timezone</span>
              <input
                aria-label="Timezone"
                value={timezone}
                onChange={(event) => setTimezone(event.target.value)}
              />
              <small>Use an IANA name such as UTC or Asia/Kolkata.</small>
            </label>
          </div>
          <fieldset className="required-fields">
            <legend>Required fields that must agree</legend>
            {comparableFields
              .filter((field) => field !== identityField)
              .map((field) => (
                <label key={field}>
                  <input
                    type="checkbox"
                    checked={requiredFields.includes(field)}
                    onChange={() => toggleRequired(field)}
                  />
                  <span>{field}</span>
                </label>
              ))}
          </fieldset>
          <button
            className="button primary-button"
            type="button"
            disabled={busy === "rule" || requiredFields.length === 0}
            onClick={() => void saveRule()}
          >
            {busy === "rule" ? "Saving rule…" : "Save rule & continue"}
          </button>
        </article>
      )}
    </section>
  );
}
