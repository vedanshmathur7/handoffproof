import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../src/App";

describe("App", () => {
  it("renders the product name and honest empty state", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: "HandoffProof" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "No reconciliation runs yet" }),
    ).toBeInTheDocument();
  });
});
