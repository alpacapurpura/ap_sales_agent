"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { TableBlock as TableBlockType } from "../../types/message-blocks";

interface TableBlockProps {
  block: TableBlockType;
  /** Highlight this row value (e.g. recommended option) */
  recommendedRow?: string;
  className?: string;
}

/**
 * Renders a data table from a TableBlock.
 * Mobile-responsive: on small screens (< 640px) renders as cards.
 */
export function TableBlock({ block, recommendedRow, className }: TableBlockProps) {
  const { columns, rows, caption } = block;

  return (
    <div className={cn("w-full space-y-1.5", className)}>
      {caption && <p className="text-xs font-medium text-muted-foreground">{caption}</p>}

      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              {columns.map((col) => (
                <TableHead key={col} className="text-xs font-medium">
                  {col}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, rowIdx) => {
              const isRecommended = recommendedRow && row[0] === recommendedRow;
              return (
                <TableRow
                  key={rowIdx}
                  className={cn(isRecommended && "bg-purple-50 dark:bg-purple-900/20 font-medium")}
                >
                  {columns.map((col, colIdx) => (
                    <TableCell key={col} className="text-xs py-1.5">
                      {row[colIdx] ?? ""}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Mobile cards */}
      <div className="sm:hidden space-y-2">
        {rows.map((row, rowIdx) => {
          const isRecommended = recommendedRow && row[0] === recommendedRow;
          return (
            <div
              key={rowIdx}
              className={cn(
                "rounded-md border border-border p-2.5 space-y-1",
                isRecommended && "border-purple-400 bg-purple-50 dark:bg-purple-900/20",
              )}
            >
              {columns.map((col, colIdx) => (
                <div key={col} className="flex gap-2 text-xs">
                  <span className="font-medium text-muted-foreground w-24 shrink-0">{col}</span>
                  <span className="text-foreground">{row[colIdx] ?? ""}</span>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

TableBlock.displayName = "TableBlock";
