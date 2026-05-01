import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number; // 0-100
  className?: string;
}

/**
 * Badge de puntuación de lead.
 * Ranges:  0–39 → secondary (gris)
 *         40–69 → default (cálido)
 *         70–100 → destructive (hot lead)
 *
 * Patrón de referencia: CampaignTag.tsx (PR-8).
 */
export function ScoreBadge({ score, className }: ScoreBadgeProps) {
  const variant = score >= 70 ? "destructive" : score >= 40 ? "default" : "secondary";

  return (
    <Badge variant={variant} className={cn("tabular-nums", className)}>
      {score}
    </Badge>
  );
}
