import { render, screen, fireEvent } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect, vi } from "vitest";

import { SelectedContactsBar } from "../SelectedContactsBar";

import type { SelectedContactsBarAction } from "../../types";

describe("SelectedContactsBar", () => {
  it("renders nothing when no IDs selected", () => {
    const { container } = render(
      <SelectedContactsBar selectedIds={[]} actions={[]} onClearSelection={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows count when IDs selected", () => {
    render(
      <SelectedContactsBar selectedIds={["a", "b", "c"]} actions={[]} onClearSelection={vi.fn()} />,
    );
    expect(screen.getByText(/3 contactos seleccionados/)).toBeInTheDocument();
  });

  it("calls onClearSelection when button clicked", () => {
    const onClear = vi.fn();
    render(<SelectedContactsBar selectedIds={["a"]} actions={[]} onClearSelection={onClear} />);
    fireEvent.click(screen.getByText("Limpiar selección"));
    expect(onClear).toHaveBeenCalledOnce();
  });

  it("renders slot actions when provided", () => {
    const actions: SelectedContactsBarAction[] = [
      {
        id: "create-segment",
        label: "Crear segmento",
        onClick: vi.fn(),
      },
    ];
    render(
      <SelectedContactsBar selectedIds={["a", "b"]} actions={actions} onClearSelection={vi.fn()} />,
    );
    expect(screen.getByText("Crear segmento")).toBeInTheDocument();
  });

  it("calls action onClick with selectedIds when clicked", () => {
    const onAction = vi.fn();
    const actions: SelectedContactsBarAction[] = [
      { id: "test", label: "Acción test", onClick: onAction },
    ];
    render(
      <SelectedContactsBar
        selectedIds={["id1", "id2"]}
        actions={actions}
        onClearSelection={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText("Acción test"));
    expect(onAction).toHaveBeenCalledWith(["id1", "id2"]);
  });

  it("shows singular form for 1 selected", () => {
    render(<SelectedContactsBar selectedIds={["a"]} actions={[]} onClearSelection={vi.fn()} />);
    expect(screen.getByText(/1 contacto seleccionado/)).toBeInTheDocument();
  });
});
