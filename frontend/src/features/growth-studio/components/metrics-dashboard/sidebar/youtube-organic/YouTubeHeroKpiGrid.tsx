"use client";

import { HeroKpiGrid } from "../shared/HeroKpiGrid";

import type { MetricKpiData, MetricTimeSeries } from "../../../../types/metrics";

const YT_HERO_METRICS = [
  "views",
  "watch_time_minutes",
  "subscribers_gained",
  "avg_view_percentage",
] as const;

export function YouTubeHeroKpiGrid({
  kpis,
  timeSeries,
}: {
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
}) {
  return (
    <HeroKpiGrid
      kpis={kpis}
      timeSeries={timeSeries}
      heroMetrics={YT_HERO_METRICS}
      gradientPrefix="yt"
      formatOptions={{ percentDecimals: 1 }}
    />
  );
}
