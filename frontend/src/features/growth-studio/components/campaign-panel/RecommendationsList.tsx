"use client";

import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { Recommendation } from "../../types/campaigns";

const IMPORTANCE_STYLES: Record<string, string> = {
  HIGH: "bg-red-100 text-red-700 border-red-200",
  MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
  LOW: "bg-blue-100 text-blue-700 border-blue-200",
};

const TYPE_LABELS: Record<string, string> = {
  CREATIVE_FATIGUE: "Fatiga creativa",
  SCALE_GOOD_CAMPAIGN: "Escalar campaña",
  AUTOMATIC_PLACEMENTS: "Ubicaciones automáticas",
  BROAD_TARGETING: "Ampliar público",
  LEARNING_LIMITED: "Aprendizaje limitado",
};

interface RecommendationsListProps {
  recommendations: Recommendation[];
}

export function RecommendationsList({ recommendations }: RecommendationsListProps) {
  if (recommendations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">
        Sin recomendaciones por ahora
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {recommendations.map((rec, idx) => {
        const importanceClass = IMPORTANCE_STYLES[rec.importance ?? ""] ?? IMPORTANCE_STYLES.LOW;
        const typeLabel = TYPE_LABELS[rec.recommendation_type] ?? rec.recommendation_type;

        return (
          <div key={`${rec.recommendation_type}-${idx}`} className="rounded-lg border p-3 text-sm">
            <div className="flex items-center gap-2 mb-1">
              {rec.importance && (
                <Badge variant="outline" className={cn("text-xs", importanceClass)}>
                  {rec.importance}
                </Badge>
              )}
              <span className="font-medium text-xs">{typeLabel}</span>
            </div>

            {rec.body && <p className="text-xs text-muted-foreground mt-1">{rec.body}</p>}

            {rec.lift_estimate && (
              <p className="text-xs text-green-600 mt-1">Estimado: {rec.lift_estimate}</p>
            )}

            {rec.url && (
              <Button variant="link" size="sm" className="h-auto p-0 mt-1 text-xs" asChild>
                <a href={rec.url} target="_blank" rel="noopener noreferrer">
                  Ver en Ads Manager <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}
