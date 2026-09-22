import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../src/App";
import { Summary } from "../src/features/reconciliations/Summary";
import type {
  ImportResult,
  ReconciliationResult,
  RunSummary,
} from "../src/types/reconciliation";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fields = [
  "source_record_id",
  "submitted_at",
  "email",
  "full_name",
  "company",
  "region",
  "transfer_enabled",
];

function imported(kind: "source" | "destination"): ImportResult {
  return {
    id: `${kind}-import-id`,
    workspace_id: "workspace-id",
    kind,
    filename: `${kind}.csv`,
    checksum: "abc",
    coverage: "complete",
    status: "completed",
    total_rows: kind === "source" ? 6 : 4,
    accepted_rows: kind === "source" ? 6 : 4,
    rejected_rows: 0,
    duplicate_rows: 0,
    schema_fields:
      kind === "source"
        ? fields
        : [
            "destination_record_id",
            "created_at",
            "email",
            "full_name",
            "company",
            "region",
          ],
    row_errors: [],
    created_at: "2026-09-22T10:00:00Z",
  };
}

const counts = {
  matched: 1,
  missing: 2,
  duplicate: 1,
  field_mismatch: 1,
  excluded: 1,
  unknown: 0,
};

const run: RunSummary = {
  id: "run-id",
  workspace_id: "workspace-id",
  source_import_id: "source-import-id",
  destination_import_id: "destination-import-id",
  rule_id: "rule-id",
  rule_version: 1,
  status: "completed",
  coverage: "complete",
  result_counts: counts,
  started_at: "2026-09-22T10:00:00Z",
  completed_at: "2026-09-22T10:00:01Z",
  created_at: "2026-09-22T10:00:00Z",
};

const result: ReconciliationResult = {
  id: "result-id",
  run_id: "run-id",
  source_observation_id: "source-observation-id",
  source_record_id: "SRC_MISMATCH",
  category: "field_mismatch",
  reason_code: "REQUIRED_FIELD_MISMATCH",
  evidence: {
    differences: [
      {
        field: "company",
        source: "correct company",
        destination: "wrong company",
      },
    ],
  },
  source_evidence: {
    email: "mismatch@example.test",
    company: "Correct Company",
  },
  candidates: [
    {
      destination_observation_id: "destination-observation-id",
      external_record_id: "DST_MISMATCH",
      rank: 1,
      match_basis: { field: "email", value: "mismatch@example.test" },
      original_evidence: {
        email: "mismatch@example.test",
        company: "Wrong Company",
      },
    },
  ],
  reviews: [],
  rule: {
    id: "rule-id",
    version: 1,
    name: "Email lead handoff",
    identity_field: "email",
    required_fields: ["full_name", "company", "region"],
    wait_seconds: 300,
    timezone: "UTC",
  },
  created_at: "2026-09-22T10:00:01Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("reconciliation flow", () => {
  it("takes a fresh reviewer from CSV files to explainable results and a review", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/workspaces")) {
        return jsonResponse({
          id: "workspace-id",
          name: "Local interview demo",
          created_at: "2026-09-22T10:00:00Z",
        });
      }
      if (url.endsWith("/api/v1/imports/source")) {
        return jsonResponse(imported("source"), 201);
      }
      if (url.endsWith("/api/v1/imports/destination")) {
        return jsonResponse(imported("destination"), 201);
      }
      if (url.endsWith("/api/v1/rules")) {
        return jsonResponse(
          {
            id: "rule-id",
            workspace_id: "workspace-id",
            version: 1,
            name: "Email lead handoff",
            eligibility: { field: "transfer_enabled", equals: "true" },
            identity_field: "email",
            required_fields: ["full_name", "company", "region"],
            wait_seconds: 300,
            timezone: "UTC",
            created_at: "2026-09-22T10:00:00Z",
          },
          201,
        );
      }
      if (url.endsWith("/api/v1/reconciliations")) {
        return jsonResponse(run, 201);
      }
      if (url.includes("/results?") && (!init?.method || init.method === "GET")) {
        return jsonResponse({ items: [result], total: 1, offset: 0, limit: 100 });
      }
      if (url.includes("/reviews")) {
        return jsonResponse(
          {
            id: "review-id",
            reviewer: "reviewer@example.test",
            annotation: "Confirmed mismatch.",
            created_at: "2026-09-22T10:01:00Z",
          },
          201,
        );
      }
      throw new Error(`Unhandled request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    await screen.findByText("Workspace ready");
    const sourceInput = screen.getByLabelText("Choose source CSV");
    const destinationInput = screen.getByLabelText("Choose destination CSV");
    fireEvent.change(sourceInput, {
      target: { files: [new File(["source"], "source.csv", { type: "text/csv" })] },
    });
    fireEvent.change(destinationInput, {
      target: {
        files: [new File(["destination"], "destination.csv", { type: "text/csv" })],
      },
    });

    const sourceCard = screen.getByRole("heading", { name: "Source submissions" })
      .closest("article")!;
    const destinationCard = screen
      .getByRole("heading", { name: "Destination contacts" })
      .closest("article")!;
    fireEvent.click(within(sourceCard).getByRole("button", { name: "Validate & import" }));
    await within(sourceCard).findByText("6");
    fireEvent.click(
      within(destinationCard).getByRole("button", { name: "Validate & import" }),
    );
    await screen.findByRole("heading", {
      name: "Define what “arrived correctly” means",
    });

    fireEvent.click(screen.getByRole("button", { name: "Save rule & continue" }));
    await screen.findByRole("heading", { name: "Run the evidence check" });
    fireEvent.click(screen.getByRole("button", { name: "Run reconciliation →" }));

    expect(
      await screen.findByRole("heading", { name: "6 source records classified" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("SRC_MISMATCH")).toHaveLength(2);
    expect(screen.getByText("REQUIRED_FIELD_MISMATCH")).toBeInTheDocument();
    expect(screen.getByText(/DST_MISMATCH/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Download results CSV" }),
    ).toHaveAttribute("download");

    fireEvent.change(screen.getByLabelText("Review note"), {
      target: { value: "Confirmed mismatch." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add review note" }));
    expect(await screen.findByText("Confirmed mismatch.")).toBeInTheDocument();
    expect(screen.getByText("REQUIRED_FIELD_MISMATCH")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it("makes partial coverage impossible to mistake for healthy", () => {
    render(
      <Summary
        run={{
          ...run,
          coverage: "partial",
          result_counts: {
            matched: 0,
            missing: 0,
            duplicate: 0,
            field_mismatch: 0,
            excluded: 0,
            unknown: 6,
          },
        }}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Do not treat this run as healthy.",
    );
    expect(screen.getByText("partial coverage")).toBeInTheDocument();
    expect(screen.getByText("6 source records classified")).toBeInTheDocument();
  });

  it("shows an honest empty result category", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/workspaces")) {
        return jsonResponse({
          id: "workspace-id",
          name: "Local interview demo",
          created_at: "2026-09-22T10:00:00Z",
        });
      }
      throw new Error("No later requests expected in this focused test.");
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await waitFor(() => expect(screen.getByText("Workspace ready")).toBeInTheDocument());
    expect(screen.queryByText("No reconciliation runs yet")).not.toBeInTheDocument();
  });
});
