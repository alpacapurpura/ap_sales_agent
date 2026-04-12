"use client";

import { useMemo } from "react";
import { CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  BRAND_SECTIONS,
  BRAND_SECTION_ORDER,
  type BrandSectionId,
  buildSectionNavItems,
} from "../../config/sections";
import type { BrandSettings } from "../../types";

interface StepGapReviewProps {
  settings: BrandSettings;
  onFinish: () => void;
}

function computeSectionHealth(sectionId: BrandSectionId, settings: BrandSettings) {
  const items = buildSectionNavItems(sectionId, settings);
  if (items.length === 0) return { score: 0, items: [] };
  const score = Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length);
  return { score, items };
}

export function StepGapReview({ settings, onFinish }: StepGapReviewProps) {
  const sectionData = useMemo(
    () =>
      BRAND_SECTION_ORDER.map((id) => ({
        id,
        config: BRAND_SECTIONS[id],
        ...computeSectionHealth(id, settings),
      })),
    [settings]
  );

  const overallScore = useMemo(() => {
    const total = sectionData.reduce((sum, s) => sum + s.score, 0);
    return Math.round(total / sectionData.length);
  }, [sectionData]);

  return (
    <div className="mx-auto max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <span className="text-2xl font-bold text-primary">{overallScore}%</span>
        </div>
        <h2 className="text-2xl font-bold text-foreground">
          {overallScore >= 80 ? "¡Excelente extracción!" : overallScore >= 40 ? "Buen inicio" : "Tenemos una base"}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {overallScore >= 80
            ? "Tu marca está casi completa. Puedes refinar los detalles desde el Brand Studio."
            : "Extrajimos lo que pudimos. Puedes completar el resto manualmente o esperar la entrevista IA (próximamente)."}
        </p>
      </div>

      <div className="space-y-3">
        {sectionData.map(({ id, config, score, items }) => (
          <div
            key={id}
            className={cn(
              "rounded-xl border p-4 transition-colors",
              score >= 80 ? "border-emerald-500/30 bg-emerald-500/5" : score > 0 ? "border-amber-500/30 bg-amber-500/5" : "border-border bg-muted/20"
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {score >= 80 ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <AlertCircle className={cn("h-5 w-5", score > 0 ? "text-amber-500" : "text-muted-foreground")} />
                )}
                <div>
                  <h3 className="font-semibold text-foreground">{config.label}</h3>
                  <p className="text-xs text-muted-foreground">{config.subtitle}</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs font-semibold",
                  score >= 80
                    ? "border-emerald-500/30 text-emerald-400"
                    : score > 0
                      ? "border-amber-500/30 text-amber-400"
                      : "text-muted-foreground"
                )}
              >
                {score}%
              </Badge>
            </div>

            {/* Sub-items detail */}
            {items.length > 0 && score < 100 && (
              <div className="mt-3 flex flex-wrap gap-1.5 pl-8">
                {items.map((item) => (
                  <Badge
                    key={item.id}
                    variant={item.status === "complete" ? "secondary" : "outline"}
                    className={cn(
                      "text-[10px]",
                      item.status === "complete" && "bg-emerald-500/10 text-emerald-400",
                      item.status === "partial" && "border-amber-500/30 text-amber-400",
                      item.status === "empty" && "text-muted-foreground"
                    )}
                  >
                    {item.status === "complete" ? "✓" : item.status === "partial" ? "◐" : "○"} {item.label}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <Button onClick={onFinish} size="lg" className="gap-2">
          Ir a mi Brand Studio
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
