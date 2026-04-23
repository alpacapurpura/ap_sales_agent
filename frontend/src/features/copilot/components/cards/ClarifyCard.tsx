"use client";

import { CheckCircle2, HelpCircle } from "lucide-react";
import { memo } from "react";

import { cn } from "@/lib/utils";

interface ClarifyItem {
  fieldPath: string;
  issue: string;
  options: string[];
}

interface ClarifyCardProps {
  items: ClarifyItem[];
  onResolve: (resolution: string) => void;
  status: "pending" | "resolved";
}

/** Must mirror MAX_CLARIFY_ITEMS in backend shared_tools/clarify.py. */
const MAX_CLARIFY_ITEMS = 4;

export const ClarifyCard = memo(function ClarifyCard({
  items,
  onResolve,
  status,
}: ClarifyCardProps) {
  const isResolved = status === "resolved";

  if (isResolved) {
    return (
      <div
        role="status"
        className={cn(
          "animate-in slide-in-from-bottom-2 fade-in duration-300",
          "inline-flex items-center gap-1.5 rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs font-medium text-success",
        )}
      >
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Listo, gracias</span>
      </div>
    );
  }

  return (
    <div
      role="group"
      aria-label="Pregunta del asistente"
      className={cn(
        "animate-in slide-in-from-bottom-2 fade-in duration-300",
        "rounded-xl border border-border bg-card p-3.5 text-card-foreground shadow-sm",
        "ring-1 ring-brand/10",
      )}
    >
      <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold text-foreground">
        <span
          className="flex h-5 w-5 items-center justify-center rounded-full bg-brand/15 text-brand"
          aria-hidden="true"
        >
          <HelpCircle className="h-3.5 w-3.5" />
        </span>
        <span>Necesito confirmar algo</span>
      </div>

      {items.slice(0, MAX_CLARIFY_ITEMS).map((item, idx) => (
        <div
          key={idx}
          className="mb-2 rounded-lg border border-border/60 bg-muted/40 p-2.5 last:mb-0"
        >
          <div className="text-xs leading-relaxed text-foreground">{item.issue}</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {item.options.map((opt, optIdx) => (
              <button
                key={optIdx}
                type="button"
                onClick={() => onResolve(opt)}
                className={cn(
                  "rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground",
                  "transition-colors duration-150 active:scale-[0.98]",
                  "hover:border-brand/60 hover:bg-brand/10 hover:text-brand",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-1 focus-visible:ring-offset-background",
                )}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
});
ClarifyCard.displayName = "ClarifyCard";
