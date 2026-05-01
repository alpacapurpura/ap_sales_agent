"use client";

import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type RowSelectionState,
} from "@tanstack/react-table";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { DataTableProps } from "./types";

const SKELETON_ROWS = 10;

/**
 * Wrapper genérico TanStack Table + Shadcn Table.
 * 100% genérico, sin business logic.
 * Maneja: sorting local, selection controlada (lifted), paginación offset.
 */
export function DataTable<TData>({
  data,
  columns,
  totalCount,
  limit,
  offset,
  onPageChange,
  onRowClick,
  selectedIds = [],
  onSelectionChange,
  getRowId,
  isLoading = false,
  emptyMessage = "No hay resultados.",
  className,
}: DataTableProps<TData>): React.ReactElement {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  // Compute row selection state from selectedIds
  const rowSelection = React.useMemo<RowSelectionState>(() => {
    const sel: RowSelectionState = {};
    for (const id of selectedIds) {
      sel[id] = true;
    }
    return sel;
  }, [selectedIds]);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      rowSelection,
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId,
    onSortingChange: setSorting,
    onRowSelectionChange: (updater) => {
      if (!onSelectionChange) return;
      const next = typeof updater === "function" ? updater(rowSelection) : updater;
      onSelectionChange(Object.keys(next).filter((id) => next[id]));
    },
    enableRowSelection: !!onSelectionChange,
    manualPagination: true,
    rowCount: totalCount,
  });

  const totalPages = Math.max(1, Math.ceil(totalCount / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  const canPrev = offset > 0;
  const canNext = offset + limit < totalCount;

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="rounded-md border">
        <Table role="table">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sortDir = header.column.getIsSorted();
                  return (
                    <TableHead
                      key={header.id}
                      scope="col"
                      aria-sort={
                        sortDir === "asc"
                          ? "ascending"
                          : sortDir === "desc"
                            ? "descending"
                            : canSort
                              ? "none"
                              : undefined
                      }
                      className={canSort ? "cursor-pointer select-none" : undefined}
                      onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                      {sortDir === "asc" ? " ↑" : sortDir === "desc" ? " ↓" : null}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody aria-busy={isLoading}>
            {isLoading ? (
              Array.from({ length: SKELETON_ROWS }).map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  {columns.map((_, ci) => (
                    <TableCell key={ci}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="py-12 text-center text-muted-foreground"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() ? "selected" : undefined}
                  className={cn(
                    "data-[state=selected]:bg-accent",
                    onRowClick ? "cursor-pointer" : undefined,
                  )}
                  onClick={onRowClick ? () => onRowClick(row.original) : undefined}
                  aria-selected={row.getIsSelected()}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-1 text-sm text-muted-foreground">
        <span>
          Mostrando {Math.min(offset + 1, totalCount)}–{Math.min(offset + limit, totalCount)} de{" "}
          {totalCount}
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(offset - limit)}
            disabled={!canPrev || isLoading}
            aria-label="Página anterior"
          >
            ‹
          </Button>
          <span className="px-2">
            {currentPage} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(offset + limit)}
            disabled={!canNext || isLoading}
            aria-label="Página siguiente"
          >
            ›
          </Button>
        </div>
      </div>
    </div>
  );
}
