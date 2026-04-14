"use client";

import { TrendingDown, TrendingUp, UserMinus, UserPlus, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MetricKpiData } from "../../../../types/metrics";

interface IgOrganicGrowthIndicatorProps {
  kpis: MetricKpiData[];
}

function formatSigned(value: number): string {
  if (value > 0) return `+${value.toLocaleString("en-US")}`;
  return value.toLocaleString("en-US");
}

export function IgOrganicGrowthIndicator({ kpis }: IgOrganicGrowthIndicatorProps) {
  const netKpi = kpis.find((k) => k.metricName === "ig_follows_and_unfollows");
  const gainedKpi = kpis.find((k) => k.metricName === "ig_follows_gained");
  const lostKpi = kpis.find((k) => k.metricName === "ig_follows_lost");

  // We must have at least gained + lost (the source of truth). The net KPI is
  // derived server-side but we recompute it client-side as a consistency guard.
  if (!gainedKpi || !lostKpi) return null;

  const gained = gainedKpi.currentValue;
  const lost = lostKpi.currentValue;
  // Prefer server-side net, but fall back to a client-side derivation so the
  // UI never renders stale data if the backend contract drifts.
  const netFollows = netKpi?.currentValue ?? gained - lost;
  const isPositive = netFollows >= 0;
  const deltaPct = netKpi?.deltaPct;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Crecimiento de Audiencia
      </h4>
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-500/10">
            <Users className="h-5 w-5 text-pink-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-muted-foreground">Seguidores netos (periodo)</p>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold tabular-nums">
                {formatSigned(netFollows)}
              </span>
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 text-xs font-medium",
                  isPositive ? "text-emerald-600" : "text-red-600",
                )}
              >
                {isPositive ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {deltaPct != null
                  ? `${Math.abs(deltaPct).toFixed(1)}% vs anterior`
                  : isPositive
                    ? "Creciendo"
                    : "Decreciendo"}
              </span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2 border-t">
          <div className="flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-emerald-600" />
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">Ganados</p>
              <p className="text-sm font-semibold tabular-nums text-emerald-600">
                +{gained.toLocaleString("en-US")}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <UserMinus className="h-4 w-4 text-red-600" />
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">Perdidos</p>
              <p className="text-sm font-semibold tabular-nums text-red-600">
                −{lost.toLocaleString("en-US")}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
