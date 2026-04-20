"use client";

import { Star, Users } from "lucide-react";
import { useCallback, type KeyboardEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

import type { BuyerPersona } from "@/lib/api/buyer-persona";

interface BuyerPersonaCardProps {
  readonly persona: BuyerPersona;
  readonly onClick: () => void;
}

const SCOPE_LABELS: Record<BuyerPersona["scope"], string> = {
  GLOBAL: "Global",
  OFFER: "Por oferta",
  CAMPAIGN: "Por campaña",
};

/** Compact card representing a single buyer persona in the index grid. */
export function BuyerPersonaCard({ persona, onClick }: BuyerPersonaCardProps) {
  const score = Math.max(0, Math.min(100, Math.round(persona.completeness_score)));
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onClick();
      }
    },
    [onClick],
  );
  return (
    <Card
      role="button"
      tabIndex={0}
      aria-label={persona.name}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={cn(
        "cursor-pointer transition-colors hover:bg-muted/50 focus-visible:outline-none",
        "focus-visible:ring-2 focus-visible:ring-ring",
      )}
    >
      <CardContent className="flex flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Users className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h3 className="truncate text-base font-semibold text-foreground">{persona.name}</h3>
              {persona.tagline && (
                <p className="truncate text-sm text-muted-foreground">{persona.tagline}</p>
              )}
            </div>
          </div>
          {persona.is_primary && (
            <Badge
              variant="secondary"
              className="shrink-0 gap-1 bg-amber-500/10 text-amber-700 dark:text-amber-300"
            >
              <Star className="h-3 w-3 fill-current" /> Principal
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {SCOPE_LABELS[persona.scope]}
          </Badge>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Perfil completo</span>
            <span className="font-medium text-foreground">{score}%</span>
          </div>
          <Progress value={score} className="h-1.5" />
        </div>
      </CardContent>
    </Card>
  );
}
