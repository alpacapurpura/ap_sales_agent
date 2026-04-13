"use client";

import { forwardRef } from "react";
import {
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

type DocumentStatus = "pending" | "processing" | "done" | "error";

interface DocumentChipProps extends React.HTMLAttributes<HTMLDivElement> {
  file: File;
  status: DocumentStatus;
  onRemove?: () => void;
}

const statusConfig: Record<
  DocumentStatus,
  { icon: React.ReactNode; label?: string; color: string }
> = {
  pending: {
    icon: <FileText className="h-3.5 w-3.5 text-gray-400" />,
    color: "border-white/10 bg-white/5",
  },
  processing: {
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-400" />,
    label: "Analizando...",
    color: "border-purple-500/30 bg-purple-500/10",
  },
  done: {
    icon: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />,
    color: "border-emerald-500/30 bg-emerald-500/10",
  },
  error: {
    icon: <XCircle className="h-3.5 w-3.5 text-red-400" />,
    color: "border-red-500/30 bg-red-500/10",
  },
};

export const DocumentChip = forwardRef<HTMLDivElement, DocumentChipProps>(
  ({ file, status, onRemove, className, ...props }, ref) => {
    const cfg = statusConfig[status];
    const showRemove = status === "pending" && !!onRemove;

    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
          cfg.color,
          className
        )}
        {...props}
      >
        {cfg.icon}
        <span className="max-w-[120px] truncate text-gray-300">
          {file.name}
        </span>
        {cfg.label && (
          <span className="text-gray-500">{cfg.label}</span>
        )}
        {showRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label="Eliminar documento"
            className="ml-0.5 rounded-full p-0.5 text-gray-500 transition-colors hover:bg-white/10 hover:text-gray-300"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
    );
  }
);
DocumentChip.displayName = "DocumentChip";
