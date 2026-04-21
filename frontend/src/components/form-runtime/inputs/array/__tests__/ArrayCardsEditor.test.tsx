import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ArrayCardsEditor } from "../ArrayCardsEditor";

import type { NestedFieldRenderer } from "../../ArrayInput";
import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

const titleField: FieldSchema = {
  id: "title",
  label: "Título",
  type: "text",
  path: "title",
  required: true,
};

const descField: FieldSchema = {
  id: "description",
  label: "Descripción",
  type: "textarea",
  path: "description",
};

const arrayField: FieldSchema = {
  id: "items",
  label: "Pilares",
  type: "array",
  path: "items",
  itemSchema: { fields: [titleField, descField] },
};

const mockRenderField: NestedFieldRenderer = ({ field, value, onChange }) => (
  <input
    data-testid={`field-${field.id}`}
    value={typeof value === "string" ? value : ""}
    onChange={(e) => onChange(e.target.value)}
  />
);

function makeItem(title: string, description?: string): Row {
  return { title, ...(description !== undefined ? { description } : {}) };
}

describe("ArrayCardsEditor", () => {
  it("renderiza N ítems con sus summaries", () => {
    const items = [makeItem("Pilar uno"), makeItem("Pilar dos")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    expect(screen.getByText("Pilar uno")).toBeTruthy();
    expect(screen.getByText("Pilar dos")).toBeTruthy();
  });

  it("click chevron expande el ítem", () => {
    const items = [makeItem("Pilar uno")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    const toggleBtn = screen.getByLabelText("Expandir ítem 1");
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId("field-title")).toBeTruthy();
  });

  it("click chevron de ítem expandido lo colapsa", () => {
    const items = [makeItem("Pilar uno")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    const toggleBtn = screen.getByLabelText("Expandir ítem 1");
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId("field-title")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Colapsar ítem 1"));
    expect(screen.queryByTestId("field-title")).toBeNull();
  });

  it("solo un ítem expandido a la vez", () => {
    const items = [makeItem("Pilar uno"), makeItem("Pilar dos")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByLabelText("Expandir ítem 1"));
    fireEvent.click(screen.getByLabelText("Expandir ítem 2"));
    // Debería haber solo 2 inputs (uno por ítem expandido), pero ítem 1 debería colapsar
    const inputs = screen.getAllByTestId("field-title");
    expect(inputs).toHaveLength(1);
  });

  it("click Agregar añade ítem y lo auto-expande", () => {
    const onChange = vi.fn();
    const items = [makeItem("Pilar uno")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={onChange}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /agregar/i }));
    expect(onChange).toHaveBeenCalledWith([makeItem("Pilar uno"), {}]);
  });

  it("click Eliminar llama onChange con el ítem removido", () => {
    const onChange = vi.fn();
    const items = [makeItem("Pilar uno"), makeItem("Pilar dos")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={onChange}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getAllByLabelText("Eliminar ítem")[0]);
    expect(onChange).toHaveBeenCalledWith([makeItem("Pilar dos")]);
  });

  it("onChange se llama con array correcto al editar campo (autosave path)", () => {
    const onChange = vi.fn();
    const items = [makeItem("Pilar uno")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={onChange}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByLabelText("Expandir ítem 1"));
    fireEvent.change(screen.getByTestId("field-title"), { target: { value: "Nuevo valor" } });
    expect(onChange).toHaveBeenCalledWith([{ ...makeItem("Pilar uno"), title: "Nuevo valor" }]);
  });

  it("badge estado se renderiza según computeItemStatus", () => {
    const items = [makeItem(""), makeItem("Pilar lleno", "Con descripción")];
    render(
      <ArrayCardsEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    // Ítem 1: sin título (required) → badge "REQUIERE"
    expect(screen.getByText(/requiere/i)).toBeTruthy();
    // Ítem 2: completo → badge "Completo"
    expect(screen.getByText("Completo")).toBeTruthy();
  });
});
