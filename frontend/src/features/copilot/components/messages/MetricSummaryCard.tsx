"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";

interface MetricSummaryCardProps {
  metrics: Array<{
    label: string;
    value: string;
    trend?: "up" | "down" | "flat";
    delta?: string;
  }>;
}

export function MetricSummaryCard({ metrics }: MetricSummaryCardProps) {
  return (
    <div className="my-1 grid grid-cols-2 gap-2">
      {metrics.map((m, idx) => {
        const TrendIcon = m.trend === "up" ? TrendingUp : m.trend === "down" ? TrendingDown : Minus;
        const trendColor =
          m.trend === "up"
            ? "text-green-500"
            : m.trend === "down"
              ? "text-red-500"
              : "text-slate-400";

        return (
          <Card key={idx} className="px-3 py-2.5">
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                {m.value}
              </span>
              <div className="flex items-center gap-1">
                {m.delta && (
                  <span className={`text-[11px] font-medium ${trendColor}`}>{m.delta}</span>
                )}
                <TrendIcon className={`h-3.5 w-3.5 ${trendColor}`} />
              </div>
            </div>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{m.label}</p>
          </Card>
        );
      })}
    </div>
  );
}
