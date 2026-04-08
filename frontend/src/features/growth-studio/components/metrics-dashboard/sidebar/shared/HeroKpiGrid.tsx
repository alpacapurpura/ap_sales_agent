'use client';

import { memo } from 'react';
import { TrendingDown, TrendingUp } from 'lucide-react';
import { Area, AreaChart } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
import { formatMetricValue } from '../../../../utils/format-metric-value';
import { BenchmarkBadge } from '../../channel-widgets/BenchmarkBadge';
import { MetricInfoCard } from '../../channel-widgets/KpiTooltip';
import type { MetricKpiData, MetricTimeSeries } from '../../../../types/metrics';

interface HeroKpiGridProps {
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
  heroMetrics: readonly string[];
  gradientPrefix: string;
  showMetricInfoCard?: boolean;
  formatOptions?: { percentDecimals?: number };
}

function HeroKpiGridInner({
  kpis,
  timeSeries,
  heroMetrics,
  gradientPrefix,
  showMetricInfoCard = true,
  formatOptions,
}: HeroKpiGridProps) {
  const heroKpis = heroMetrics
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

        const formattedValue = formatMetricValue(kpi.currentValue, kpi.unit, {
          currency: kpi.currency,
          percentDecimals: formatOptions?.percentDecimals,
        });

        const gradientId = `${gradientPrefix}-grad-${kpi.metricName}`;

        const label = <p className="text-xs text-muted-foreground">{kpi.displayName}</p>;

        return (
          <div
            key={kpi.metricName}
            className="rounded-lg border bg-card p-3 space-y-1.5"
          >
            {showMetricInfoCard ? (
              <MetricInfoCard metricName={kpi.metricName}>
                {label}
              </MetricInfoCard>
            ) : (
              label
            )}
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-semibold tabular-nums">
                {formattedValue}
              </span>
              {sparkData.length > 2 && (
                <ChartContainer
                  config={{ v: { color: 'hsl(var(--primary))' } }}
                  className="h-7 w-[80px] !aspect-auto"
                >
                  <AreaChart data={sparkData}>
                    <defs>
                      <linearGradient
                        id={gradientId}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="var(--color-v)"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="100%"
                          stopColor="var(--color-v)"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="v"
                      stroke="var(--color-v)"
                      strokeWidth={1.5}
                      fill={`url(#${gradientId})`}
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
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {Math.abs(kpi.deltaPct).toFixed(1)}%
                </span>
              )}
              {kpi.benchmark && (
                <BenchmarkBadge
                  value={kpi.currentValue}
                  benchmark={kpi.benchmark}
                  higherIsBetter={kpi.higherIsBetter}
                />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export const HeroKpiGrid = memo(HeroKpiGridInner);
HeroKpiGrid.displayName = 'HeroKpiGrid';
