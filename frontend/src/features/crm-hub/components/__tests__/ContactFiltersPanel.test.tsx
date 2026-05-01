import { render, screen, fireEvent } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect, vi } from "vitest";

import { ContactFiltersPanel } from "../ContactFiltersPanel";

import type { ContactFilterParams } from "../../types";

describe("ContactFiltersPanel", () => {
  it("renders without errors", () => {
    render(<ContactFiltersPanel filters={{}} onChange={vi.fn()} />);
    expect(screen.getByText("Filtros")).toBeInTheDocument();
  });

  it("shows 'Limpiar' button when filters are active", () => {
    render(<ContactFiltersPanel filters={{ lifecycle_stage_in: ["lead"] }} onChange={vi.fn()} />);
    expect(screen.getByText("Limpiar")).toBeInTheDocument();
  });

  it("does not show 'Limpiar' button when no filters active", () => {
    render(<ContactFiltersPanel filters={{}} onChange={vi.fn()} />);
    expect(screen.queryByText("Limpiar")).not.toBeInTheDocument();
  });

  it("calls onChange with empty object when Limpiar clicked", () => {
    const onChange = vi.fn();
    render(<ContactFiltersPanel filters={{ is_inactive: true }} onChange={onChange} />);
    fireEvent.click(screen.getByText("Limpiar"));
    expect(onChange).toHaveBeenCalledWith({});
  });

  it("calls onChange with updated is_inactive when checkbox checked", () => {
    const onChange = vi.fn();
    render(<ContactFiltersPanel filters={{}} onChange={onChange} />);
    const checkbox = screen.getByLabelText("Inactivos");
    fireEvent.click(checkbox);
    expect(onChange).toHaveBeenCalled();
    const call = onChange.mock.calls[0][0] as ContactFilterParams;
    expect(call.is_inactive).toBe(true);
  });

  it("renders all filter sections", () => {
    render(<ContactFiltersPanel filters={{}} onChange={vi.fn()} />);
    // Filter labels
    expect(screen.getByText("Etapa")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
    expect(screen.getByText("Canales")).toBeInTheDocument();
    expect(screen.getByText("Otros")).toBeInTheDocument();
    expect(screen.getByText("País")).toBeInTheDocument();
  });
});
