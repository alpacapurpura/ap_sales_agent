import type { ColumnDef } from "@tanstack/react-table";

export interface DataTableProps<TData> {
  data: TData[];
  columns: ColumnDef<TData>[];
  totalCount: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
  onRowClick?: (row: TData) => void;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  getRowId: (row: TData) => string;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}
