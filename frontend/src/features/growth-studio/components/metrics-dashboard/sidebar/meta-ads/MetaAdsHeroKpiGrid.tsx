"use client";

import { HeroKpiGrid } from "../shared/HeroKpiGrid";

import type { MetricKpiData, MetricTimeSeries } from "../../../../types/metrics";

const META_HERO_METRICS = ["spend", "ROAS", "CPL", "CTR"] as const;

export function MetaAdsHeroKpiGrid({
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
      heroMetrics={META_HERO_METRICS}
      gradientPrefix="meta"
      showMetricInfoCard={false}
    />
  );
}
