import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";

import { SectionShell } from "./SectionShell";

describe("SectionShell", () => {
  it("renders title", () => {
    render(<SectionShell title="General">child</SectionShell>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("General");
  });

  it("renders description when provided", () => {
    render(
      <SectionShell title="Test" description="A description here">
        child
      </SectionShell>,
    );
    expect(screen.getByText("A description here")).toBeInTheDocument();
  });

  it("does not render description paragraph when omitted", () => {
    render(<SectionShell title="Test">child</SectionShell>);
    expect(screen.queryByText(/description/i)).not.toBeInTheDocument();
  });

  it("renders children", () => {
    render(
      <SectionShell title="Test">
        <span data-testid="child">content</span>
      </SectionShell>,
    );
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });
});
