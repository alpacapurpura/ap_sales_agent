"use client";

import { ArrowRight } from "lucide-react";

import type { MiniFunnelData } from "../../../types/metrics";

interface MiniFunnelProps {
  data: MiniFunnelData;
}

export function MiniFunnel({ data }: MiniFunnelProps) {
  return (
    <div className="flex items-center gap-3 px-3 py-3 bg-muted/30 rounded-lg">
      <div className="flex flex-col items-center">
        <span className="text-xs text-muted-foreground">{data.sourceLabel}</span>
        <span className="text-xl font-semibold tabular-nums">
          {data.sourceValue.toLocaleString("es-ES")}
        </span>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground" />
      <div className="flex flex-col items-center">
        <span className="text-xs text-muted-foreground">{data.targetLabel}</span>
        <span className="text-xl font-semibold tabular-nums">
          {data.targetValue.toLocaleString("es-ES")}
        </span>
      </div>
      <span className="text-muted-foreground mx-1">=</span>
      <span className="text-xl font-semibold text-primary">{data.conversionRate.toFixed(1)}%</span>
    </div>
  );
}
