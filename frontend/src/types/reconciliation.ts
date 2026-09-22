export type Coverage = "complete" | "partial" | "failed";
export type Category =
  | "matched"
  | "missing"
  | "duplicate"
  | "field_mismatch"
  | "excluded"
  | "unknown";

export const categories: Category[] = [
  "matched",
  "missing",
  "duplicate",
  "field_mismatch",
  "excluded",
  "unknown",
];

export interface Workspace {
  id: string;
  name: string;
  created_at: string;
}

export interface RowError {
  row_number: number;
  code: string;
}

export interface ImportResult {
  id: string;
  workspace_id: string;
  kind: "source" | "destination";
  filename: string;
  checksum: string;
  coverage: Coverage;
  status: "pending" | "completed" | "failed";
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  duplicate_rows: number;
  schema_fields: string[];
  row_errors: RowError[];
  created_at: string;
}

export interface Eligibility {
  field: string;
  equals: string;
}

export interface RuleResult {
  id: string;
  workspace_id: string;
  version: number;
  name: string;
  eligibility: Eligibility;
  identity_field: string;
  required_fields: string[];
  wait_seconds: number;
  timezone: string;
  created_at: string;
}

export interface RunSummary {
  id: string;
  workspace_id: string;
  source_import_id: string;
  destination_import_id: string;
  rule_id: string;
  rule_version: number;
  status: "pending" | "running" | "completed" | "failed";
  coverage: Coverage;
  result_counts: Record<Category, number>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface RuleReference {
  id: string;
  version: number;
  name: string;
  identity_field: string;
  required_fields: string[];
  wait_seconds: number;
  timezone: string;
}

export interface Candidate {
  destination_observation_id: string;
  external_record_id: string;
  rank: number;
  match_basis: Record<string, unknown>;
  original_evidence: Record<string, unknown>;
}

export interface Review {
  id: string;
  reviewer: string;
  annotation: string;
  created_at: string;
}

export interface ReconciliationResult {
  id: string;
  run_id: string;
  source_observation_id: string;
  source_record_id: string;
  category: Category;
  reason_code: string;
  evidence: Record<string, unknown>;
  source_evidence: Record<string, unknown>;
  candidates: Candidate[];
  reviews: Review[];
  rule: RuleReference;
  created_at: string;
}

export interface ResultPage {
  items: ReconciliationResult[];
  total: number;
  offset: number;
  limit: number;
}

export interface ApiFailure {
  code: string;
  message: string;
  details?: unknown;
}
