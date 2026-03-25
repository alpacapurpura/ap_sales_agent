"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface ComparisonTableProps {
  columns: string[];
  rows: Array<Record<string, string>>;
  recommended?: string;
}

export function ComparisonTable({
  columns,
  rows,
  recommended,
}: ComparisonTableProps) {
  return (
    <div className="my-1 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col) => (
              <TableHead key={col} className="text-xs">
                {col}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, idx) => {
            const isRecommended =
              recommended &&
              Object.values(row).some((v) => v === recommended);
            return (
              <TableRow
                key={idx}
                className={
                  isRecommended
                    ? "bg-purple-50 dark:bg-purple-900/20"
                    : undefined
                }
              >
                {columns.map((col) => (
                  <TableCell key={col} className="text-xs">
                    {row[col] ?? "\u2014"}
                    {isRecommended && col === columns[0] && (
                      <Badge
                        variant="secondary"
                        className="ml-1.5 bg-purple-100 text-[10px] text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
                      >
                        Recomendado
                      </Badge>
                    )}
                  </TableCell>
                ))}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
