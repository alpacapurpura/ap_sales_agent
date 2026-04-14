"use client";

import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";

import { cn } from "@/lib/utils";
import type { FrequencyAlert, MetricKpiData } from "../../../../types/metrics";

interface ReachFrequencySectionProps {
  kpis: MetricKpiData[];
  frequencyAlert: FrequencyAlert | null;
}

function FrequencyGauge({ value }: { value: number }) {
  const pct = Math.min((value / 6) * 100, 100);
  const color = value < 3 ? "bg-emerald-500" : value < 5 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="space-y-1">
      {/* Gauge bar */}
      <div className="relative h-3 w-full rounded-full overflow-hidden">
        {/* Zone backgrounds */}
        <div className="absolute inset-0 flex">
          <div className="bg-emerald-500/20" style={{ width: "50%" }} />
          <div className="bg-amber-500/20" style={{ width: "33.3%" }} />
          <div className="bg-red-500/20" style={{ width: "16.7%" }} />
        </div>
        {/* Current value indicator */}
        <div
          className={cn("absolute top-0 h-full rounded-full", color)}
          style={{ width: `${Math.max(pct, 3)}%` }}
        />
      </div>
      {/* Scale labels */}
      <div className="flex justify-between text-[9px] text-muted-foreground tabular-nums">
        <span>0</span>
        <span style={{ marginLeft: "47%" }}>3</span>
        <span>5+</span>
      </div>
    </div>
  );
}

export function ReachFrequencySection({ kpis, frequencyAlert }: ReachFrequencySectionProps) {
  const reach = kpis.find((k) => k.metricName === "reach");
  const frequency = kpis.find((k) => k.metricName === "frequency");

  if (!reach && !frequency) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Alcance y Frecuencia
      </h4>
      <div className="grid grid-cols-2 gap-3">
        {reach && (
          <div className="rounded-lg border bg-card p-3 space-y-1">
            <p className="text-xs text-muted-foreground">Alcance</p>
            <p className="text-lg font-semibold tabular-nums">
              {reach.currentValue.toLocaleString("en-US")}
            </p>
            <p className="text-[10px] text-muted-foreground">Personas únicas — no es suma diaria</p>
            {reach.deltaPct != null && (
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 text-[10px] font-medium",
                  reach.deltaPct >= 0 ? "text-emerald-500" : "text-red-500",
                )}
              >
                {reach.deltaPct >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {Math.abs(reach.deltaPct).toFixed(1)}% vs anterior
              </span>
            )}
          </div>
        )}
        {frequency && (
          <div className="rounded-lg border bg-card p-3 space-y-1">
            <p className="text-xs text-muted-foreground">Frecuencia</p>
            <p className="text-lg font-semibold tabular-nums">
              {frequency.currentValue.toFixed(2)}x
            </p>
            <FrequencyGauge value={frequency.currentValue} />
            {frequencyAlert && (
              <div
                className={cn(
                  "flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium",
                  frequencyAlert.severity === "critical"
                    ? "bg-red-500/10 text-red-600"
                    : "bg-amber-500/10 text-amber-600",
                )}
              >
                <AlertTriangle className="h-3 w-3" />
                {frequencyAlert.message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
