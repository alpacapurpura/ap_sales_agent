"use client";

import { AlertTriangle } from "lucide-react";

import type { BottleneckData } from "../../../types/metrics";

interface BottleneckBannerProps {
  bottleneck: BottleneckData;
}

/**
 *
 */
export function BottleneckBanner({ bottleneck }: BottleneckBannerProps) {
  const { metricLabel, currentRate, severity, threshold, tip } = bottleneck;

  const bgColor =
    severity === "critical"
      ? "bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-800"
      : "bg-yellow-50 border-yellow-200 dark:bg-yellow-950/20 dark:border-yellow-800";
  const textColor =
    severity === "critical"
      ? "text-red-800 dark:text-red-200"
      : "text-yellow-800 dark:text-yellow-200";

  return (
    <div className={`rounded-lg border p-3 ${bgColor}`} role="alert">
      <div className="flex items-center gap-2">
        <AlertTriangle className={`h-4 w-4 ${textColor}`} />
        <span className={`text-sm font-semibold ${textColor}`}>
          {metricLabel}: {currentRate.toFixed(1)}% ({">"} {threshold}%)
        </span>
      </div>
      <p className="text-xs text-muted-foreground mt-1">{tip}</p>
    </div>
  );
}
