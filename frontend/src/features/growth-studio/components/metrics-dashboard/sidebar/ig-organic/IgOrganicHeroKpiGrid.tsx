'use client';

import { TrendingDown, TrendingUp } from 'lucide-react';
import { Area, AreaChart } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
import { BenchmarkBadge } from '../../channel-widgets/BenchmarkBadge';
import { MetricInfoCard } from '../../channel-widgets/KpiTooltip';
import type { MetricKpiData, MetricTimeSeries } from '../../../../types/metrics';

interface IgOrganicHeroKpiGridProps {
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
}

const HERO_METRICS = ['total_interactions', 'ig_views', 'ig_follows_and_unfollows', 'ig_engagement_rate'];

function formatValue(value: number, unit: string): string {
  if (unit === 'currency')
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (unit === 'percentage') return `${value.toFixed(2)}%`;
  if (unit === 'ratio') return `${value.toFixed(2)}x`;
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
  return value.toLocaleString('en-US');
}

export function IgOrganicHeroKpiGrid({ kpis, timeSeries }: IgOrganicHeroKpiGridProps) {
  const heroKpis = HERO_METRICS
    .map(name => kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  return (
    <div className="grid grid-cols-2 gap-3">
      {heroKpis.map(kpi => {
        const spark = timeSeries.find(ts => ts.metricName === kpi.metricName);
        const sparkData = spark?.dataPoints.map(p => ({ v: p.value })) ?? [];
        const isPositive =
          kpi.deltaPct != null &&
          (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);

        return (
          <div
            key={kpi.metricName}
            className="rounded-lg border bg-card p-3 space-y-1.5"
          >
            <MetricInfoCard metricName={kpi.metricName}>
              <p className="text-xs text-muted-foreground">{kpi.displayName}</p>
            </MetricInfoCard>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-semibold tabular-nums">
                {formatValue(kpi.currentValue, kpi.unit)}
              </span>
              {sparkData.length > 2 && (
                <ChartContainer
                  config={{ v: { color: 'hsl(var(--primary))' } }}
                  className="h-7 w-[80px] !aspect-auto"
                >
                  <AreaChart data={sparkData}>
                    <defs>
                      <linearGradient
                        id={`ig-grad-${kpi.metricName}`}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop offset="0%" stopColor="var(--color-v)" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="var(--color-v)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="v"
                      stroke="var(--color-v)"
                      strokeWidth={1.5}
                      fill={`url(#ig-grad-${kpi.metricName})`}
                    />
                  </AreaChart>
                </ChartContainer>
              )}
            </div>
            <div className="flex items-center gap-2">
              {kpi.deltaPct != null && (
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 text-xs font-medium',
                    isPositive ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(kpi.deltaPct).toFixed(1)}%
                </span>
              )}
              {kpi.benchmark && (
                <BenchmarkBadge value={kpi.currentValue} benchmark={kpi.benchmark} higherIsBetter={kpi.higherIsBetter} />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
