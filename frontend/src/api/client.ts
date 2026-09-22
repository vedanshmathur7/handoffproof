import type {
  ApiFailure,
  Category,
  Coverage,
  ImportResult,
  ResultPage,
  Review,
  RuleResult,
  RunSummary,
  Workspace,
} from "../types/reconciliation";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  details?: unknown;

  constructor(failure: ApiFailure) {
    super(failure.message);
    this.name = "ApiError";
    this.code = failure.code;
    this.details = failure.details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let failure: ApiFailure = {
      code: "NETWORK_REQUEST_FAILED",
      message: `Request failed with HTTP ${response.status}.`,
    };
    try {
      failure = (await response.json()) as ApiFailure;
    } catch {
      // Keep the stable local fallback when a proxy returns non-JSON.
    }
    throw new ApiError(failure);
  }
  return (await response.json()) as T;
}

export function createWorkspace(name = "Local interview demo"): Promise<Workspace> {
  return request<Workspace>("/api/v1/workspaces", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function uploadImport(
  workspaceId: string,
  kind: "source" | "destination",
  file: File,
  coverage: Coverage,
): Promise<ImportResult> {
  const body = new FormData();
  body.set("workspace_id", workspaceId);
  body.set("coverage", coverage);
  body.set("file", file);
  return request<ImportResult>(`/api/v1/imports/${kind}`, {
    method: "POST",
    body,
  });
}

export interface CreateRuleInput {
  workspace_id: string;
  source_import_id: string;
  destination_import_id: string;
  name: string;
  eligibility: { field: string; equals: string };
  identity_field: string;
  required_fields: string[];
  wait_seconds: number;
  timezone: string;
}

export function createRule(input: CreateRuleInput): Promise<RuleResult> {
  return request<RuleResult>("/api/v1/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function createRun(
  workspaceId: string,
  sourceImportId: string,
  destinationImportId: string,
  ruleId: string,
  idempotencyKey: string,
): Promise<RunSummary> {
  return request<RunSummary>("/api/v1/reconciliations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      source_import_id: sourceImportId,
      destination_import_id: destinationImportId,
      rule_id: ruleId,
      idempotency_key: idempotencyKey,
    }),
  });
}

export function getResults(
  workspaceId: string,
  runId: string,
  category?: Category,
): Promise<ResultPage> {
  const params = new URLSearchParams({ workspace_id: workspaceId, limit: "100" });
  if (category) params.set("category", category);
  return request<ResultPage>(
    `/api/v1/reconciliations/${runId}/results?${params.toString()}`,
  );
}

export function addReview(
  workspaceId: string,
  resultId: string,
  reviewer: string,
  annotation: string,
): Promise<Review> {
  return request<Review>(`/api/v1/results/${resultId}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: workspaceId, reviewer, annotation }),
  });
}

export function exportUrl(workspaceId: string, runId: string): string {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  return `${API_BASE}/api/v1/reconciliations/${runId}/export?${params.toString()}`;
}
