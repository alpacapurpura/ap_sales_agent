"use client";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export interface OfferProgressBarProps {
  percentage: number;
  completed: number;
  total: number;
  nextMilestone?: string | null;
  className?: string;
}

/**
 * Inline progress display for the Offer Studio shell header (Row 2).
 *
 * Renders the tabular percentage, the Shadcn progress bar and a small
 * "N de M secciones · Siguiente: {milestone}" counter on the right.
 */
export function OfferProgressBar({
  percentage,
  completed,
  total,
  nextMilestone,
  className,
}: OfferProgressBarProps) {
  const safePercent = Math.max(0, Math.min(100, percentage));

  return (
    <div
      className={cn(
        "flex min-w-0 flex-1 items-center gap-3",
        className,
      )}
      role="group"
      aria-label="Progreso de la oferta"
    >
      <span className="shrink-0 text-sm font-bold tabular-nums text-primary">
        {safePercent}%
      </span>
      <Progress
        value={safePercent}
        className="h-2 flex-1"
        aria-label="Porcentaje completado"
      />
      <p className="shrink-0 truncate text-xs text-muted-foreground">
        <span className="tabular-nums">
          {completed} de {total} secciones
        </span>
        {nextMilestone ? (
          <>
            <span className="mx-1">·</span>
            <span>Siguiente: {nextMilestone}</span>
          </>
        ) : null}
      </p>
    </div>
  );
}
