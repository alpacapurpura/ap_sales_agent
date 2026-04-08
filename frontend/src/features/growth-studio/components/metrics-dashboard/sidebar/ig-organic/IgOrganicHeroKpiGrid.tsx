'use client';

import { HeroKpiGrid } from '../shared/HeroKpiGrid';
import type { MetricKpiData, MetricTimeSeries } from '../../../../types/metrics';

const IG_HERO_METRICS = ['total_interactions', 'ig_views', 'ig_follows_and_unfollows', 'ig_engagement_rate'] as const;

export function IgOrganicHeroKpiGrid({ kpis, timeSeries }: { kpis: MetricKpiData[]; timeSeries: MetricTimeSeries[] }) {
  return <HeroKpiGrid kpis={kpis} timeSeries={timeSeries} heroMetrics={IG_HERO_METRICS} gradientPrefix="ig" />;
}
