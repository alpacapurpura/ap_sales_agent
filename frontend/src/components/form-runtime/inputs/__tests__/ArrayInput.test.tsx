import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ArrayInput } from "../ArrayInput";

import type { NestedFieldRenderer } from "../ArrayInput";
import type { FieldSchema } from "@/lib/form-runtime/schema";

const mockRenderField: NestedFieldRenderer = ({ field }) => (
  <div data-testid={`nested-${field.id}`} />
);

function makeArrayField(fieldCount: number): FieldSchema {
  const fields = Array.from({ length: fieldCount }, (_, i) => ({
    id: `f${i}`,
    label: `Campo ${i}`,
    type: "text" as const,
    path: `f${i}`,
    required: false,
  }));

  return {
    id: "arr",
    label: "Items",
    type: "array",
    path: "arr",
    itemSchema: { fields },
  };
}

describe("ArrayInput — dispatcher", () => {
  it("renderiza ArrayCardsEditor para schema de 2 campos", () => {
    const field = makeArrayField(2);
    render(
      <ArrayInput
        field={field}
        value={[{ f0: "uno" }]}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    // Cards: no split-panel search. Counter renders "1 ítem".
    expect(screen.queryByPlaceholderText(/buscar/i)).toBeNull();
    expect(screen.getByText(/1 ítem/)).toBeTruthy();
  });

  it("renderiza ArraySplitEditor para schema de 5 campos", () => {
    const field = makeArrayField(5);
    render(
      <ArrayInput
        field={field}
        value={[{ f0: "uno" }]}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    // Split: has search input
    expect(screen.getByPlaceholderText(/buscar/i)).toBeTruthy();
  });

  it("renderiza ArrayCardsEditor para schema de 3 campos (límite exacto)", () => {
    const field = makeArrayField(3);
    render(
      <ArrayInput field={field} value={[]} onChange={vi.fn()} renderField={mockRenderField} />,
    );
    // Cards — no search
    expect(screen.queryByPlaceholderText(/buscar/i)).toBeNull();
  });

  it("renderiza ArraySplitEditor para schema de 4 campos (límite exacto)", () => {
    const field = makeArrayField(4);
    render(
      <ArrayInput field={field} value={[]} onChange={vi.fn()} renderField={mockRenderField} />,
    );
    // Split — has search
    expect(screen.getByPlaceholderText(/buscar/i)).toBeTruthy();
  });

  it("muestra error cuando falta itemSchema", () => {
    const field: FieldSchema = {
      id: "arr",
      label: "Array",
      type: "array",
      path: "arr",
    };
    render(
      <ArrayInput field={field} value={[]} onChange={vi.fn()} renderField={mockRenderField} />,
    );
    expect(screen.getByText(/Schema error/i)).toBeTruthy();
  });
});
