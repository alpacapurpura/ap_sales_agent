"use client";

import { forwardRef } from "react";

import { cn } from "@/lib/utils";

import { AttachmentChip } from "./AttachmentChip";

import type { AttachmentChipFile } from "./AttachmentChip";

// ── Types ────────────────────────────────────────────────────────────

interface AttachmentTrayProps extends React.HTMLAttributes<HTMLDivElement> {
  attachments: AttachmentChipFile[];
  onCancel: (id: string) => void;
  onRemove: (id: string) => void;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Horizontal flex-wrap tray containing one AttachmentChip per file.
 * Hidden when the attachments array is empty.
 */
export const AttachmentTray = forwardRef<HTMLDivElement, AttachmentTrayProps>(
  ({ attachments, onCancel, onRemove, className, ...props }, ref) => {
    if (attachments.length === 0) return null;

    return (
      <div
        ref={ref}
        role="list"
        aria-label="Archivos adjuntos"
        className={cn("flex flex-wrap gap-1.5 px-3 py-2 border-t border-border", className)}
        {...props}
      >
        {attachments.map((attachment) => (
          <AttachmentChip
            key={attachment.id}
            attachment={attachment}
            onCancel={onCancel}
            onRemove={onRemove}
          />
        ))}
      </div>
    );
  },
);
AttachmentTray.displayName = "AttachmentTray";
