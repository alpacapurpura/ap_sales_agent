"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { PreviewSummaryProps } from "@/features/copilot/config/interview-preview-registry";

// ── Helpers ─────────────────────────────────────────────────────────────────

function getInitial(name: string | undefined): string {
  if (!name || name.trim().length === 0) return "?";
  return name.trim().charAt(0).toUpperCase();
}

// ── Component ───────────────────────────────────────────────────────────────

export const PersonaPreviewSummary = forwardRef<HTMLDivElement, PreviewSummaryProps>(
  ({ data, completenessScore, ...props }, ref) => {
    const name = (data.name as string) || "";
    const tagline = (data.tagline as string) || "";
    const displayName = name || "Buyer Persona";
    const initial = getInitial(name);

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center gap-4 px-5 py-4 border-b border-white/5",
          "bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-indigo-500/5",
        )}
        {...props}
      >
        {/* Avatar circle */}
        <div
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-full",
            "bg-gradient-to-br from-indigo-500 to-purple-600",
            "text-lg font-bold text-white",
          )}
        >
          {initial}
        </div>

        {/* Name + tagline */}
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-semibold text-foreground truncate">{displayName}</span>
          {tagline && <span className="text-xs text-muted-foreground truncate">{tagline}</span>}
        </div>

        {/* Completeness score badge */}
        <Badge
          variant="secondary"
          className="ml-auto shrink-0 bg-purple-500/20 text-purple-300 border-purple-500/30"
        >
          {completenessScore}%
        </Badge>
      </div>
    );
  },
);

PersonaPreviewSummary.displayName = "PersonaPreviewSummary";
