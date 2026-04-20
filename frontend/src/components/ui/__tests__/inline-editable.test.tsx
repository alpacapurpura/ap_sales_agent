import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InlineEditableInput, InlineEditableTextarea } from "../inline-editable";

describe("InlineEditableTextarea", () => {
  it("renders the value and placeholder", () => {
    render(
      <InlineEditableTextarea
        value="Historia larga…"
        onChange={vi.fn()}
        placeholder="Escribe…"
        aria-label="historia"
      />,
    );
    expect(screen.getByDisplayValue("Historia larga…")).toBeTruthy();
  });

  it("fires onChange when typing", () => {
    const onChange = vi.fn();
    render(
      <InlineEditableTextarea value="" onChange={onChange} aria-label="x" />,
    );
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "nuevo" } });
    expect(onChange).toHaveBeenCalledWith("nuevo");
  });

  it("accepts tone variant classes", () => {
    const { container } = render(
      <InlineEditableTextarea value="" onChange={vi.fn()} tone="xl" aria-label="y" />,
    );
    const textarea = container.querySelector("textarea");
    expect(textarea?.className).toContain("text-xl");
  });
});

describe("InlineEditableInput", () => {
  it("renders as a single-line input", () => {
    render(<InlineEditableInput value="Alpaca" onChange={vi.fn()} aria-label="name" />);
    const input = screen.getByDisplayValue("Alpaca");
    expect(input.tagName).toBe("INPUT");
  });

  it("supports type=url", () => {
    render(
      <InlineEditableInput
        value="https://x.lat"
        onChange={vi.fn()}
        type="url"
        aria-label="site"
      />,
    );
    expect(screen.getByDisplayValue("https://x.lat").getAttribute("type")).toBe("url");
  });
});
