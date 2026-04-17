"use client";

import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { useArchetypeDisplay } from "@/features/offer-studio/hooks/use-archetype-display";
import { useValueLevelMetadata } from "@/features/offer-studio/hooks/use-value-level-catalog";
import { cn } from "@/lib/utils";

import type { PreviewSummaryProps } from "@/features/copilot/config/interview-preview-registry";
import type { OfferArchetype, OfferValueLevel } from "@/features/offer-studio/types";

// ── Helpers ──────────────────────────────────────────────────────────────────

interface ParsedSummary {
  name: string | null;
  archetype: OfferArchetype | null;
  valueLevel: string | null;
  price: number | null;
  currency: string | null;
}

function parseSummaryData(data: Record<string, unknown>): ParsedSummary {
  const name = (data.public_name as string) ?? null;
  const archetype = (data.archetype as OfferArchetype) ?? null;
  const valueLevel = (data.value_level as string) ?? null;

  // Extract price from pricing_options array
  let price: number | null = null;
  let currency: string | null = null;
  const pricing = data.pricing_options as
    | { total_amount?: number; currency?: string }[]
    | undefined;
  if (pricing && pricing.length > 0) {
    price = pricing[0].total_amount ?? null;
    currency = pricing[0].currency ?? null;
  }

  return { name, archetype, valueLevel, price, currency };
}

// ── Component ────────────────────────────────────────────────────────────────

export function OfferPreviewSummary({ data, completenessScore }: PreviewSummaryProps) {
  const summary = useMemo(() => parseSummaryData(data), [data]);

  const archetypeDisplay = useArchetypeDisplay(summary.archetype ?? undefined);
  const valueLevelMeta = useValueLevelMetadata(
    (summary.valueLevel as OfferValueLevel | null) ?? undefined,
  );

  const ArchetypeIcon = archetypeDisplay?.icon ?? null;

  return (
    <div className="px-4 py-3 border-b border-white/5 bg-background/50">
      <div className="flex items-start gap-3">
        {/* Archetype icon */}
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
            "bg-gradient-to-br from-orange-500 to-amber-500 text-white",
          )}
        >
          {ArchetypeIcon ? (
            <ArchetypeIcon className="h-5 w-5" />
          ) : (
            <span className="text-sm font-bold">?</span>
          )}
        </div>

        {/* Name + tags */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground truncate">
            {summary.name ?? <span className="italic text-muted-foreground">Pendiente...</span>}
          </p>

          <div className="mt-1 flex flex-wrap gap-1.5">
            {archetypeDisplay && (
              <Badge
                variant="secondary"
                className="text-[10px] bg-orange-500/10 text-orange-400 border-orange-500/20"
              >
                {archetypeDisplay.label}
              </Badge>
            )}
            {summary.valueLevel && (
              <Badge
                variant="secondary"
                className="text-[10px] bg-amber-500/10 text-amber-400 border-amber-500/20"
              >
                {valueLevelMeta?.label_es ?? summary.valueLevel}
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Price + completeness */}
      <div className="mt-2 flex items-center justify-between">
        <div>
          {summary.price !== null && (
            <span className="text-sm font-bold text-foreground">
              {summary.currency ?? "USD"} {summary.price.toLocaleString()}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Completitud</span>
          <span className="text-xs font-semibold text-orange-400">{completenessScore}%</span>
        </div>
      </div>
    </div>
  );
}
