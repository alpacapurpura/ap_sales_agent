"use client";

import { CheckCircle2, Sparkles, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { PendienteItem } from "./PendienteItem";

import type { PendingReason } from "./PendienteItem";
import type { CampaignWithMetrics } from "../../../../../types/metrics";

export interface PendingCampaign {
  campaign: CampaignWithMetrics;
  reason: PendingReason;
}

type FilterType = "all" | "no_offer" | "no_utm";

interface PendientesListProps {
  items: PendingCampaign[];
  currency: string;
  selectedId: string | null;
  onSelect: (externalId: string) => void;
  isLoading: boolean;
  onAutoDetect: () => void;
  isAutoDetecting: boolean;
  onBackToCampaigns: () => void;
}

export function PendientesList({
  items,
  currency,
  selectedId,
  onSelect,
  isLoading,
  onAutoDetect,
  isAutoDetecting,
  onBackToCampaigns,
}: PendientesListProps) {
  const [filter, setFilter] = useState<FilterType>("all");

  const counts = useMemo(() => {
    const noOffer = items.filter((i) => i.reason === "no_offer").length;
    const noUtm = items.filter((i) => i.reason === "no_utm").length;
    return { noOffer, noUtm, total: items.length };
  }, [items]);

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    return items.filter((i) => i.reason === filter);
  }, [items, filter]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-4 py-3 border-b border-zinc-800">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-1.5 mt-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
        </div>
        <div className="p-4 space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            Pendientes
            {counts.total > 0 && (
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 text-[10px] font-bold">
                {counts.total}
              </span>
            )}
          </h2>
          {counts.noOffer > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAutoDetect}
              disabled={isAutoDetecting}
              className="h-7 gap-1 text-[10px]"
            >
              {isAutoDetecting ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3" />
              )}
              Auto-detectar
            </Button>
          )}
        </div>

        {/* Filter pills */}
        <div className="flex gap-1.5">
          {counts.noOffer > 0 && (
            <button
              type="button"
              onClick={() => setFilter((f) => (f === "no_offer" ? "all" : "no_offer"))}
              className={cn(
                "rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors",
                filter === "no_offer"
                  ? "bg-amber-500/15 border border-amber-500/30 text-amber-400"
                  : "bg-zinc-800 border border-zinc-700 text-zinc-500 hover:text-zinc-400",
              )}
            >
              Sin offer ({counts.noOffer})
            </button>
          )}
          {counts.noUtm > 0 && (
            <button
              type="button"
              onClick={() => setFilter((f) => (f === "no_utm" ? "all" : "no_utm"))}
              className={cn(
                "rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors",
                filter === "no_utm"
                  ? "bg-blue-500/15 border border-blue-500/30 text-blue-400"
                  : "bg-zinc-800 border border-zinc-700 text-zinc-500 hover:text-zinc-400",
              )}
            >
              Sin UTM ({counts.noUtm})
            </button>
          )}
          {filter !== "all" && (
            <button
              type="button"
              onClick={() => setFilter("all")}
              className="rounded-full bg-zinc-800 border border-zinc-700 px-2.5 py-0.5 text-[10px] text-zinc-500 hover:text-zinc-400"
            >
              Todos
            </button>
          )}
        </div>
      </div>

      {/* List or empty state */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 mb-3" />
            <p className="text-sm font-medium">¡Todo resuelto!</p>
            <p className="text-xs text-muted-foreground mt-1">
              No hay campañas pendientes de configuración.
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onBackToCampaigns}
              className="mt-4 text-xs"
            >
              Volver a Campañas
            </Button>
          </div>
        ) : (
          filtered.map((item) => (
            <PendienteItem
              key={item.campaign.externalId}
              campaign={item.campaign}
              reason={item.reason}
              currency={currency}
              isSelected={selectedId === item.campaign.externalId}
              onClick={() => onSelect(item.campaign.externalId)}
            />
          ))
        )}
      </div>
    </div>
  );
}
