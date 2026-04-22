"use client";

import { FileText, FileVideo, FileAudio, Image, File, X, AlertCircle } from "lucide-react";
import { forwardRef } from "react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────────────

export type AttachmentStatus = "pending" | "uploading" | "uploaded" | "error";

export interface AttachmentChipFile {
  id: string;
  file: File;
  status: AttachmentStatus;
  progress?: number;
  error?: string;
  result?: { asset_id: string; public_url: string; mime: string };
}

interface AttachmentChipProps extends React.HTMLAttributes<HTMLDivElement> {
  attachment: AttachmentChipFile;
  onCancel: (id: string) => void;
  onRemove: (id: string) => void;
}

// ── Helpers ──────────────────────────────────────────────────────────

function getMimeIcon(mime: string): React.ReactNode {
  if (mime.startsWith("image/")) return <Image className="h-3.5 w-3.5" aria-hidden="true" />;
  if (mime.startsWith("video/")) return <FileVideo className="h-3.5 w-3.5" aria-hidden="true" />;
  if (mime.startsWith("audio/")) return <FileAudio className="h-3.5 w-3.5" aria-hidden="true" />;
  if (mime === "application/pdf") return <FileText className="h-3.5 w-3.5" aria-hidden="true" />;
  return <File className="h-3.5 w-3.5" aria-hidden="true" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Single attachment chip showing file name, size, upload progress and status.
 * Image files show a small inline preview thumbnail.
 */
export const AttachmentChip = forwardRef<HTMLDivElement, AttachmentChipProps>(
  ({ attachment, onCancel, onRemove, className, ...props }, ref) => {
    const { id, file, status, progress = 0, error } = attachment;

    const isImage = file.type.startsWith("image/");
    const previewUrl = isImage && status !== "error" ? URL.createObjectURL(file) : null;

    const handleAction = () => {
      if (status === "uploading" || status === "pending") {
        onCancel(id);
      } else {
        onRemove(id);
      }
    };

    const statusLabel =
      status === "pending"
        ? "pendiente"
        : status === "uploading"
          ? `subiendo ${progress}%`
          : status === "error"
            ? "error"
            : "listo";

    return (
      <div
        ref={ref}
        role="listitem"
        aria-label={`Archivo adjunto: ${file.name}, ${statusLabel}`}
        className={cn(
          "relative flex items-center gap-1.5 rounded-md border border-border bg-muted/40 px-2 py-1 text-xs",
          status === "error" && "border-destructive/60 bg-destructive/5",
          className,
        )}
        {...props}
      >
        {/* Preview or icon */}
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- thumbnail in chat composer, not content
          <img
            src={previewUrl}
            alt=""
            aria-hidden="true"
            className="h-7 w-7 rounded object-cover shrink-0"
            onLoad={() => URL.revokeObjectURL(previewUrl)}
          />
        ) : (
          <span
            className={cn(
              "shrink-0 text-muted-foreground",
              status === "error" && "text-destructive",
            )}
          >
            {status === "error" ? (
              <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              getMimeIcon(file.type)
            )}
          </span>
        )}

        {/* File info */}
        <div className="flex min-w-0 flex-col">
          <span className="max-w-[120px] truncate font-medium text-foreground">{file.name}</span>
          {status === "error" ? (
            <span className="text-[10px] text-destructive">{error ?? "Error al subir"}</span>
          ) : (
            <span className="text-[10px] text-muted-foreground">{formatSize(file.size)}</span>
          )}
        </div>

        {/* Cancel / remove button */}
        <button
          type="button"
          onClick={handleAction}
          aria-label={
            status === "uploading" || status === "pending"
              ? `Cancelar subida de ${file.name}`
              : `Eliminar ${file.name}`
          }
          className="ml-0.5 shrink-0 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <X className="h-3 w-3" aria-hidden="true" />
        </button>

        {/* Progress bar */}
        {status === "uploading" && (
          <div
            className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden rounded-b-md"
            aria-hidden="true"
          >
            <Progress value={progress} className="h-0.5 rounded-none" />
          </div>
        )}
      </div>
    );
  },
);
AttachmentChip.displayName = "AttachmentChip";
