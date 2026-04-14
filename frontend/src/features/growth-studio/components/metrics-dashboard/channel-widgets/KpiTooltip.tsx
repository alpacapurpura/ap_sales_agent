"use client";

import type { ReactNode } from "react";
import { Info, TrendingUp, TrendingDown } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useMetricCatalog } from "../../../hooks/useMetricCatalog";

interface MetricInfoCardProps {
  metricName: string;
  children: ReactNode;
}

export function MetricInfoCard({ metricName, children }: MetricInfoCardProps) {
  const { getTooltipData } = useMetricCatalog();
  const data = getTooltipData(metricName);

  if (!data) return <>{children}</>;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <span className="inline-flex items-center gap-0.5 cursor-help">
          {children}
          <Info className="h-3 w-3 text-muted-foreground shrink-0" />
        </span>
      </PopoverTrigger>
      <PopoverContent className="max-w-[320px] p-3 text-xs space-y-2" side="top" align="start">
        <p className="font-semibold text-sm text-foreground">{data.displayName}</p>

        {data.formula && (
          <p className="font-mono text-[11px] text-muted-foreground bg-muted/50 rounded px-1.5 py-1">
            {data.formula}
          </p>
        )}

        <p className="text-muted-foreground leading-relaxed">{data.description}</p>

        {data.benchmarks && (
          <p className="text-muted-foreground leading-relaxed border-t border-border pt-2">
            <span className="font-medium text-foreground">Referencia: </span>
            {data.benchmarks.replace(/^Referencia:?\s*/i, "")}
          </p>
        )}

        {data.interpretation && (
          <p className="text-muted-foreground leading-relaxed border-t border-border pt-2">
            {data.interpretation}
          </p>
        )}

        <div className="flex items-center gap-1 text-[11px] text-muted-foreground border-t border-border pt-2">
          {data.higherIsBetter ? (
            <>
              <TrendingUp className="h-3 w-3 text-emerald-500" />
              <span>Mas es mejor</span>
            </>
          ) : (
            <>
              <TrendingDown className="h-3 w-3 text-amber-500" />
              <span>Menos es mejor</span>
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

/** Legacy wrapper for backward compatibility */
export function KpiTooltip({ label, hint }: { label: string; hint: string }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <span className="inline-flex items-center gap-1 cursor-help">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</span>
          <Info className="h-3 w-3 text-muted-foreground" />
        </span>
      </PopoverTrigger>
      <PopoverContent className="max-w-[240px] text-xs">{hint}</PopoverContent>
    </Popover>
  );
}
