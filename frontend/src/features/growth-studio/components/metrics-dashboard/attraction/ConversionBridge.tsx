"use client";

import { ArrowRight, TrendingUp, TrendingDown } from "lucide-react";
import { memo } from "react";

interface ConversionBridgeProps {
  impressions: number;
  visitors: number;
  leads: number;
  /** Previous period values for computing deltas */
  previousVisitRate?: number | null;
  previousLeadRate?: number | null;
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toLocaleString("es-ES");
}

export const ConversionBridge = memo(function ConversionBridge({
  impressions,
  visitors,
  leads,
  previousVisitRate,
  previousLeadRate,
}: ConversionBridgeProps) {
  const visitRate = impressions > 0 ? (visitors / impressions) * 100 : 0;
  const leadRate = visitors > 0 ? (leads / visitors) * 100 : 0;

  const visitDelta = previousVisitRate != null ? visitRate - previousVisitRate : null;
  const leadDelta = previousLeadRate != null ? leadRate - previousLeadRate : null;

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <p className="text-[11px] text-muted-foreground uppercase tracking-widest font-medium mb-3">
        Puente de Conversión
      </p>

      {/* Desktop layout */}
      <div className="hidden md:flex items-center gap-3">
        {/* Impressions */}
        <div className="flex-1">
          <p className="text-sm font-semibold mb-1">{formatNum(impressions)} impresiones</p>
          <div className="w-full bg-muted rounded-full h-2.5">
            <div className="bg-blue-500 h-full rounded-full" style={{ width: "100%" }} />
          </div>
        </div>

        {/* Visit rate */}
        <RatePill rate={visitRate} label="visit rate" delta={visitDelta} />

        {/* Visitors */}
        <div className="flex-1">
          <p className="text-sm font-semibold mb-1">{formatNum(visitors)} visitas</p>
          <div className="w-full bg-muted rounded-full h-2.5">
            <div className="bg-blue-400 h-full rounded-full" style={{ width: "100%" }} />
          </div>
        </div>

        {/* Lead rate */}
        <RatePill rate={leadRate} label="lead rate" delta={leadDelta} />

        {/* Leads */}
        <div className="flex-[0.4]">
          <p className="text-sm font-semibold mb-1">{formatNum(leads)} leads</p>
          <div className="w-full bg-muted rounded-full h-2.5">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: "100%" }} />
          </div>
        </div>
      </div>

      {/* Mobile layout - stacked */}
      <div className="md:hidden space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">{formatNum(impressions)} impresiones</span>
          <span className="text-sm font-bold text-emerald-500">{visitRate.toFixed(1)}%</span>
          <span className="text-sm font-semibold">{formatNum(visitors)} visitas</span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-400 h-full rounded-full"
            style={{ width: `${Math.min(visitRate * 4, 100)}%` }}
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">{formatNum(visitors)} visitas</span>
          <span className="text-sm font-bold text-emerald-500">{leadRate.toFixed(1)}%</span>
          <span className="text-sm font-semibold">{formatNum(leads)} leads</span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-400 to-emerald-500 h-full rounded-full"
            style={{ width: `${Math.min(leadRate * 10, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
});

function RatePill({ rate, label, delta }: { rate: number; label: string; delta: number | null }) {
  const isPositive = delta != null && delta >= 0;

  return (
    <div className="flex flex-col items-center shrink-0 px-2">
      <span className="text-lg font-bold text-emerald-500">{rate.toFixed(1)}%</span>
      <span className="text-[10px] text-muted-foreground">{label}</span>
      {delta != null && (
        <span
          className={`flex items-center gap-0.5 text-[10px] font-medium ${isPositive ? "text-emerald-500/70" : "text-red-500/70"}`}
        >
          {isPositive ? (
            <TrendingUp className="h-2.5 w-2.5" />
          ) : (
            <TrendingDown className="h-2.5 w-2.5" />
          )}
          {delta >= 0 ? "+" : ""}
          {delta.toFixed(1)}pp
        </span>
      )}
      <ArrowRight className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
    </div>
  );
}
