"use client";

import { X } from "lucide-react";

import { cn } from "@/lib/utils";

export interface ReplyRef {
  messageId: string;
  preview: string;
  role: "user" | "assistant";
}

interface ReplyPreviewProps {
  replyTo: ReplyRef;
  onCancel: () => void;
  className?: string;
}

/**
 * Shows a preview strip of the message being replied to.
 * Displayed between AttachmentTray and Toolbar.
 */
export function ReplyPreview({ replyTo, onCancel, className }: ReplyPreviewProps) {
  const roleLabel = replyTo.role === "user" ? "Tú" : "Copilot";

  return (
    <div
      aria-label={`Respondiendo a ${roleLabel}`}
      className={cn(
        "flex items-start gap-2 rounded-r-md border-l-2 border-accent bg-accent/5 px-3 py-1.5",
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-medium text-muted-foreground">
          Respondiendo a: <span className="text-accent">{roleLabel}</span>
        </p>
        <p className="truncate text-xs text-foreground">&ldquo;{replyTo.preview}&rdquo;</p>
      </div>
      <button
        type="button"
        onClick={onCancel}
        aria-label="Cancelar respuesta"
        className="mt-0.5 shrink-0 rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
      >
        <X className="h-3 w-3" aria-hidden="true" />
      </button>
    </div>
  );
}

ReplyPreview.displayName = "ReplyPreview";
