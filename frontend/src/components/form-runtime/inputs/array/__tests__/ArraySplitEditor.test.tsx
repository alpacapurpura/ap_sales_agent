import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ArraySplitEditor } from "../ArraySplitEditor";

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

const categoryField: FieldSchema = {
  id: "category",
  label: "Categoría",
  type: "text",
  path: "category",
};

const statusField: FieldSchema = {
  id: "status",
  label: "Estado",
  type: "text",
  path: "status",
};

const arrayField: FieldSchema = {
  id: "items",
  label: "Casos de éxito",
  type: "array",
  path: "items",
  itemSchema: { fields: [titleField, descField, categoryField, statusField] },
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

describe("ArraySplitEditor", () => {
  it("lista muestra todos los ítems", () => {
    const items = [makeItem("Caso uno"), makeItem("Caso dos"), makeItem("Caso tres")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    expect(screen.getByText("Caso uno")).toBeTruthy();
    expect(screen.getByText("Caso dos")).toBeTruthy();
    expect(screen.getByText("Caso tres")).toBeTruthy();
  });

  it("click en ítem de lista selecciona y muestra editor", () => {
    const items = [makeItem("Caso uno"), makeItem("Caso dos")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByText("Caso uno"));
    expect(screen.getByTestId("field-title")).toBeTruthy();
  });

  it("click Agregar añade ítem y lo auto-selecciona", () => {
    const onChange = vi.fn();
    const items = [makeItem("Caso uno")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={onChange}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /agregar/i }));
    expect(onChange).toHaveBeenCalledWith([makeItem("Caso uno"), {}]);
  });

  it("onChange al editar campo propaga correctamente", () => {
    const onChange = vi.fn();
    const items = [makeItem("Caso uno")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={onChange}
        renderField={mockRenderField}
      />,
    );
    fireEvent.click(screen.getByText("Caso uno"));
    fireEvent.change(screen.getByTestId("field-title"), { target: { value: "Nuevo título" } });
    expect(onChange).toHaveBeenCalledWith([{ ...makeItem("Caso uno"), title: "Nuevo título" }]);
  });

  it("search filtra la lista de ítems", () => {
    const items = [makeItem("Caso de marketing"), makeItem("Caso de ventas")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    const searchInput = screen.getByPlaceholderText(/buscar/i);
    fireEvent.change(searchInput, { target: { value: "marketing" } });
    expect(screen.getByText("Caso de marketing")).toBeTruthy();
    expect(screen.queryByText("Caso de ventas")).toBeNull();
  });

  it("muestra empty state cuando no hay ítem seleccionado", () => {
    const items = [makeItem("Caso uno")];
    render(
      <ArraySplitEditor
        field={arrayField}
        value={items}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    expect(screen.getByText(/selecciona un ítem/i)).toBeTruthy();
  });

  it("muestra empty state cuando no hay ítems", () => {
    render(
      <ArraySplitEditor
        field={arrayField}
        value={[]}
        onChange={vi.fn()}
        renderField={mockRenderField}
      />,
    );
    expect(screen.getByText(/selecciona un ítem/i)).toBeTruthy();
  });
});
