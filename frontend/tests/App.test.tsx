import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../src/App";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App bootstrap", () => {
  it("creates an isolated demo workspace and shows the guided imports", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          id: "workspace-12345678",
          name: "Local interview demo",
          created_at: "2026-09-22T10:00:00Z",
        }),
      ),
    );
    render(<App />);

    expect(
      screen.getByText("Preparing a private demo workspace…"),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Bring both sides of the handoff" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Workspace ready")).toBeInTheDocument();
    expect(screen.getByLabelText("Choose source CSV")).toBeInTheDocument();
    expect(screen.getByLabelText("Choose destination CSV")).toBeInTheDocument();
  });

  it("shows a retry path when workspace creation fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ code: "DB_DOWN", message: "Database unavailable." }, 503),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: "workspace-retry",
          name: "Local interview demo",
          created_at: "2026-09-22T10:00:00Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    expect(await screen.findByText("Database unavailable.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry workspace setup" }));
    await waitFor(() => expect(screen.getByText("Workspace ready")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
