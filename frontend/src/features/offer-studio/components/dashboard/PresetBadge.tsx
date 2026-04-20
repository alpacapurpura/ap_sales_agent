"use client";

import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { useOfferTypePresetCatalogAll } from "@/features/offer-studio/hooks/use-offer-type-preset-catalog";
import { cn } from "@/lib/utils";

interface PresetBadgeProps {
  /** ``preset_id`` persisted on the Offer. Null/undefined → renders nothing. */
  presetId: string | null | undefined;
  /** Optional className override — keeps the badge composable in crowded
   *  layouts (dashboard card vs. detail hero). */
  className?: string;
  /** Compact mode for dense cards (10px font). Default is slightly larger. */
  compact?: boolean;
}

/**
 * Visual tag that surfaces the ``OfferTypePreset`` assigned to an offer.
 *
 * Reads the full preset catalog (cached for an hour in React Query) and
 * finds the preset by id. Shows the preset's ``label_es`` (in the user's
 * vocabulary) — not the internal ``archetype`` tag. If the preset is not
 * found (catalog out of sync, preset removed) the badge renders nothing,
 * avoiding a visible error state on legacy dashboards.
 *
 * Why the "all" hook: this component lives inside a dashboard card that
 * does not know the tenant's ``business_types``, so we use the global
 * catalog. The hit overhead is one cached query per session.
 */
export function PresetBadge({ presetId, className, compact }: PresetBadgeProps) {
  const { data } = useOfferTypePresetCatalogAll();
  if (!presetId) return null;
  const preset = data?.presets.find((p) => p.preset_id === presetId);
  if (!preset) return null;

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border-transparent bg-emerald-50 text-emerald-800 font-medium dark:bg-emerald-950 dark:text-emerald-200",
        compact ? "text-[10px] h-5 px-1.5 py-0" : "text-xs h-6 px-2 py-0.5",
        className,
      )}
      title={preset.description_es}
    >
      <Sparkles className={cn(compact ? "h-2.5 w-2.5" : "h-3 w-3")} aria-hidden />
      {preset.label_es}
    </Badge>
  );
}
