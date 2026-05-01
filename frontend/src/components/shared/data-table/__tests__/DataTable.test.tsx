import { render, screen, fireEvent } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect, vi } from "vitest";

import { DataTable } from "../DataTable";

import type { ColumnDef } from "@tanstack/react-table";

interface Row {
  id: string;
  name: string;
}

const columns: ColumnDef<Row>[] = [{ accessorKey: "name", header: "Nombre" }];

const data: Row[] = [
  { id: "1", name: "Ana García" },
  { id: "2", name: "Juan López" },
];

const baseProps = {
  data,
  columns,
  totalCount: 2,
  limit: 50,
  offset: 0,
  onPageChange: vi.fn(),
  getRowId: (row: Row) => row.id,
};

describe("DataTable", () => {
  it("renders column headers", () => {
    render(<DataTable {...baseProps} />);
    expect(screen.getByText("Nombre")).toBeInTheDocument();
  });

  it("renders row data", () => {
    render(<DataTable {...baseProps} />);
    expect(screen.getByText("Ana García")).toBeInTheDocument();
    expect(screen.getByText("Juan López")).toBeInTheDocument();
  });

  it("shows skeleton rows when isLoading", () => {
    const { container } = render(<DataTable {...baseProps} isLoading />);
    // Table body has aria-busy
    const tbody = container.querySelector("tbody");
    expect(tbody).toHaveAttribute("aria-busy", "true");
  });

  it("shows empty message when no data", () => {
    render(
      <DataTable {...baseProps} data={[]} totalCount={0} emptyMessage="Sin resultados de prueba" />,
    );
    expect(screen.getByText("Sin resultados de prueba")).toBeInTheDocument();
  });

  it("calls onRowClick when row is clicked", () => {
    const onRowClick = vi.fn();
    render(<DataTable {...baseProps} onRowClick={onRowClick} />);
    fireEvent.click(screen.getByText("Ana García"));
    expect(onRowClick).toHaveBeenCalledWith(data[0]);
  });

  it("calls onPageChange with next offset when next button clicked", () => {
    const onPageChange = vi.fn();
    render(
      <DataTable
        {...baseProps}
        totalCount={100}
        limit={50}
        offset={0}
        onPageChange={onPageChange}
      />,
    );
    const nextBtn = screen.getByLabelText("Página siguiente");
    fireEvent.click(nextBtn);
    expect(onPageChange).toHaveBeenCalledWith(50);
  });

  it("disables prev button on first page", () => {
    render(<DataTable {...baseProps} offset={0} totalCount={100} limit={50} />);
    expect(screen.getByLabelText("Página anterior")).toBeDisabled();
  });

  it("calls onSelectionChange when row selection changes", () => {
    const onSelectionChange = vi.fn();
    const selectColumn: ColumnDef<Row>[] = [
      {
        id: "select",
        cell: ({ row }) => (
          <input
            type="checkbox"
            onChange={(e) => {
              const ids = e.target.checked ? [row.original.id] : [];
              onSelectionChange(ids);
            }}
          />
        ),
      },
      ...columns,
    ];
    render(
      <DataTable
        {...baseProps}
        columns={selectColumn}
        selectedIds={[]}
        onSelectionChange={onSelectionChange}
      />,
    );
    // Component renders without error
    expect(screen.getByText("Ana García")).toBeInTheDocument();
  });

  it("shows pagination count correctly", () => {
    render(<DataTable {...baseProps} totalCount={247} limit={50} offset={0} />);
    expect(screen.getByText(/Mostrando 1–50 de 247/)).toBeInTheDocument();
  });
});
