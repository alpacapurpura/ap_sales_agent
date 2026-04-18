import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { FieldRenderer } from "../FieldRenderer";

describe("FieldRenderer", () => {
  it("dispatches to TextInput for type=text", () => {
    render(
      <FieldRenderer
        field={{ id: "n", label: "N", type: "text", path: "n" }}
        value="x"
        onChange={vi.fn()}
      />,
    );
    const input = screen.getByDisplayValue("x") as HTMLInputElement;
    expect(input.type).toBe("text");
  });

  it("dispatches to TextareaInput for type=textarea", () => {
    render(
      <FieldRenderer
        field={{ id: "m", label: "M", type: "textarea", path: "m", rows: 2 }}
        value="body"
        onChange={vi.fn()}
      />,
    );
    const ta = screen.getByDisplayValue("body");
    expect(ta.getAttribute("rows")).toBe("2");
  });

  it("dispatches to NumberInput for type=number", () => {
    render(
      <FieldRenderer
        field={{ id: "n", label: "N", type: "number", path: "n" }}
        value={5}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("spinbutton")).toBeTruthy();
  });

  it("dispatches to BooleanInput for type=boolean", () => {
    render(
      <FieldRenderer
        field={{ id: "f", label: "F", type: "boolean", path: "f" }}
        value={true}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("switch")).toBeTruthy();
  });
});
