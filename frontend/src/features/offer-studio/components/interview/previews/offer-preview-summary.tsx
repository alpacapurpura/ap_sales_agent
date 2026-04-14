"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { PreviewSummaryProps } from "@/features/copilot/config/interview-preview-registry";
import { ARCHETYPE_METADATA } from "@/features/offer-studio/config/archetype-metadata";
import type { OfferArchetype } from "@/features/offer-studio/types";

// ── Value level display names ────────────────────────────────────────────────

const VALUE_LEVEL_LABELS: Record<string, string> = {
  lead_magnet: "Lead Magnet",
  activacion: "Activaci\u00f3n",
  transformacion: "Transformaci\u00f3n",
  maximizacion: "Maximizaci\u00f3n",
  corporativo: "Corporativo",
};

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
    | Array<{ total_amount?: number; currency?: string }>
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

  const archetypeMeta = summary.archetype ? ARCHETYPE_METADATA[summary.archetype] : null;

  const ArchetypeIcon = archetypeMeta?.icon ?? null;

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
            {archetypeMeta && (
              <Badge
                variant="secondary"
                className="text-[10px] bg-orange-500/10 text-orange-400 border-orange-500/20"
              >
                {archetypeMeta.label}
              </Badge>
            )}
            {summary.valueLevel && (
              <Badge
                variant="secondary"
                className="text-[10px] bg-amber-500/10 text-amber-400 border-amber-500/20"
              >
                {VALUE_LEVEL_LABELS[summary.valueLevel] ?? summary.valueLevel}
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
