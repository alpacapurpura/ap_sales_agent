"use client";

import {
  Download,
  ExternalLink,
  File,
  FileSpreadsheet,
  FileText,
  Presentation,
  Table2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { DocumentBlock as DocumentBlockType } from "../../types/message-blocks";

interface DocumentBlockProps {
  block: DocumentBlockType;
  className?: string;
}

function getDocIcon(mime: string, filename: string): React.ReactNode {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  if (mime === "application/pdf" || ext === "pdf") {
    return <FileText className="h-5 w-5 text-red-500" aria-hidden="true" />;
  }
  if (mime.includes("spreadsheet") || mime.includes("excel") || ext === "xlsx" || ext === "xls") {
    return <FileSpreadsheet className="h-5 w-5 text-green-600" aria-hidden="true" />;
  }
  if (mime.includes("csv") || ext === "csv") {
    return <Table2 className="h-5 w-5 text-green-500" aria-hidden="true" />;
  }
  if (mime.includes("presentation") || ext === "pptx" || ext === "ppt") {
    return <Presentation className="h-5 w-5 text-orange-500" aria-hidden="true" />;
  }
  if (mime.startsWith("text/") || ext === "txt" || ext === "md") {
    return <FileText className="h-5 w-5 text-muted-foreground" aria-hidden="true" />;
  }
  return <File className="h-5 w-5 text-muted-foreground" aria-hidden="true" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Document block with icon, filename, size, and open/download actions.
 */
export function DocumentBlock({ block, className }: DocumentBlockProps) {
  const handleOpen = () => {
    window.open(block.url, "_blank", "noopener,noreferrer");
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border border-border bg-muted/40 p-3 max-w-[320px]",
        className,
      )}
    >
      <div className="mt-0.5 shrink-0">{getDocIcon(block.mime, block.filename)}</div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground">{block.filename}</p>
        <p className="text-xs text-muted-foreground">{formatSize(block.size_bytes)}</p>

        <div className="mt-2 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleOpen}
            className="h-7 gap-1 px-2 text-xs"
            aria-label={`Abrir ${block.filename}`}
          >
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
            Abrir
          </Button>
          <a
            href={block.url}
            download={block.filename}
            className="inline-flex h-7 items-center gap-1 rounded-md border border-border px-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
            aria-label={`Descargar ${block.filename}`}
          >
            <Download className="h-3 w-3" aria-hidden="true" />
            Descargar
          </a>
        </div>
      </div>
    </div>
  );
}

DocumentBlock.displayName = "DocumentBlock";
