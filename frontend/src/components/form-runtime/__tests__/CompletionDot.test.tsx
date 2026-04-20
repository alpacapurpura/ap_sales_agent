import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { CompletionDot } from "../CompletionDot";

describe("CompletionDot", () => {
  it("renders a filled dot when state=filled", () => {
    const { container } = render(<CompletionDot state="filled" />);
    const dot = container.querySelector("span");
    expect(dot).toBeTruthy();
    expect(dot?.className).toMatch(/bg-\[hsl\(var\(--success\)\)\]|bg-success/);
  });

  it("renders an empty dot when state=empty", () => {
    const { container } = render(<CompletionDot state="empty" />);
    const dot = container.querySelector("span");
    expect(dot?.className).toMatch(/bg-destructive/);
  });

  it("exposes an aria-label describing the completeness state", () => {
    const { getByLabelText } = render(<CompletionDot state="filled" />);
    expect(getByLabelText(/completo/i)).toBeTruthy();
  });

  it("exposes an aria-label for empty state", () => {
    const { getByLabelText } = render(<CompletionDot state="empty" />);
    expect(getByLabelText(/vac[íi]o|sin completar/i)).toBeTruthy();
  });
});
