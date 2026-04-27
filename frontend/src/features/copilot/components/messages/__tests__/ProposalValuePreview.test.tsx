import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProposalValuePreview } from "../ProposalValuePreview";

describe("ProposalValuePreview", () => {
  it("renders a string verbatim", () => {
    render(<ProposalValuePreview value="Valeria Fundadora" />);
    expect(screen.getByText("Valeria Fundadora")).toBeDefined();
  });

  it("renders an empty marker for null / empty string", () => {
    const { rerender } = render(<ProposalValuePreview value={null} />);
    expect(screen.getByText(/vacío/i)).toBeDefined();
    rerender(<ProposalValuePreview value="" />);
    expect(screen.getByText(/vacío/i)).toBeDefined();
  });

  it("renders an array of strings as a bullet list", () => {
    render(<ProposalValuePreview value={["foco claro", "ganar libertad"]} />);
    expect(screen.getByText("foco claro")).toBeDefined();
    expect(screen.getByText("ganar libertad")).toBeDefined();
    const items = screen.getAllByRole("listitem");
    expect(items.length).toBe(2);
  });

  it("renders an array of pain_points objects with description + severity badge", () => {
    render(
      <ProposalValuePreview
        value={[
          { description: "No tener foco claro", severity: 5 },
          { description: "Hacer mucho y no avanzar", severity: 4 },
        ]}
      />,
    );
    expect(screen.getByText("No tener foco claro")).toBeDefined();
    expect(screen.getByText("Hacer mucho y no avanzar")).toBeDefined();
    expect(screen.getByText("5/5")).toBeDefined();
    expect(screen.getByText("4/5")).toBeDefined();
  });

  it("renders an arbitrary object as a key/value list", () => {
    render(<ProposalValuePreview value={{ awareness: "se da cuenta", decision: "elige" }} />);
    expect(screen.getByText("Awareness:")).toBeDefined();
    expect(screen.getByText("se da cuenta")).toBeDefined();
    expect(screen.getByText("Decision:")).toBeDefined();
    expect(screen.getByText("elige")).toBeDefined();
  });

  it("does not leak JSON-stringified blobs into the DOM", () => {
    const { container } = render(
      <ProposalValuePreview value={[{ description: "X", severity: 5 }]} />,
    );
    expect(container.textContent).not.toContain('{"description"');
    expect(container.textContent).not.toContain("\\");
  });

  it("renders a plain number", () => {
    render(<ProposalValuePreview value={42} />);
    expect(screen.getByText("42")).toBeDefined();
  });
});
