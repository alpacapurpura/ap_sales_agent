'use client';

import { HeroKpiGrid } from '../shared/HeroKpiGrid';
import type { MetricKpiData, MetricTimeSeries } from '../../../../types/metrics';

const MAIL_HERO_METRICS = ['open_rate', 'click_rate', 'emails_sent', 'active_subscribers'] as const;

export function MailHeroKpiGrid({ kpis, timeSeries }: { kpis: MetricKpiData[]; timeSeries: MetricTimeSeries[] }) {
  return <HeroKpiGrid kpis={kpis} timeSeries={timeSeries} heroMetrics={MAIL_HERO_METRICS} gradientPrefix="mail" />;
}
