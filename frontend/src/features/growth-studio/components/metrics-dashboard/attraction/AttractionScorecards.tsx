'use client';

import { useMemo } from 'react';
import { Area, AreaChart } from 'recharts';
import { ChartContainer } from '@/components/ui/chart';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { StageTimeSeries } from '../../../types/metrics';
import { MetricInfoCard } from '../channel-widgets/KpiTooltip';

interface AttractionScorecardsProps {
  timeSeries: StageTimeSeries | undefined;
  totalImpressions: number;
  totalVisitors: number;
  totalLeads: number;
  leadConvRate: number;
  totalSpend: number;
}

interface ScorecardData {
  label: string;
  value: number;
  format: 'number' | 'percent' | 'money';
  delta: number | null;
  sparkData: { v: number }[];
  metricName?: string;
}

function formatValue(value: number, format: 'number' | 'percent' | 'money'): string {
  if (format === 'percent') return `${value.toFixed(1)}%`;
  if (format === 'money') {
    if (value === 0) return '--';
    return `$${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })}`;
  }
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toLocaleString('es-ES');
}

function computeDelta(current: number, previous: number | null): number | null {
  if (previous === null || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

export function AttractionScorecards({
  timeSeries,
  totalImpressions,
  totalVisitors,
  totalLeads,
  leadConvRate,
  totalSpend,
}: AttractionScorecardsProps) {
  const cards = useMemo((): ScorecardData[] => {
    // Build sparkline from timeseries data (sum all channels per day)
    const dailyTotals = (timeSeries?.dataPoints ?? []).map((dp) => ({
      v: Object.values(dp.channels).reduce((sum, val) => sum + val, 0),
    }));

    // Compute deltas from previous period
    const currTotal = timeSeries
      ? Object.values(timeSeries.periodTotals).reduce((s, v) => s + v, 0)
      : 0;
    const prevTotal = timeSeries?.previousPeriodTotals
      ? Object.values(timeSeries.previousPeriodTotals).reduce((s, v) => s + v, 0)
      : null;
    const reachDelta = computeDelta(currTotal, prevTotal);

    const cpl = totalLeads > 0 && totalSpend > 0 ? totalSpend / totalLeads : 0;

    return [
      {
        label: 'Impresiones',
        value: totalImpressions,
        format: 'number',
        delta: reachDelta,
        sparkData: dailyTotals,
        metricName: 'impressions',
      },
      {
        label: 'Visitantes',
        value: totalVisitors,
        format: 'number',
        delta: null,
        sparkData: [],
        metricName: 'users',
      },
      {
        label: 'Leads',
        value: totalLeads,
        format: 'number',
        delta: null,
        sparkData: [],
      },
      {
        label: 'Conv. %',
        value: leadConvRate,
        format: 'percent',
        delta: null,
        sparkData: [],
      },
      {
        label: 'CPL',
        value: cpl,
        format: 'money',
        delta: null,
        sparkData: [],
      },
    ];
  }, [timeSeries, totalImpressions, totalVisitors, totalLeads, leadConvRate, totalSpend]);

  const sparkConfig = { v: { color: 'hsl(var(--primary))' } };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-card border border-border rounded-lg p-4 flex flex-col gap-1"
        >
          {card.metricName ? (
            <MetricInfoCard metricName={card.metricName}>
              <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
                {card.label}
              </span>
            </MetricInfoCard>
          ) : (
            <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
              {card.label}
            </span>
          )}
          <div className="flex items-end justify-between gap-2">
            <span className="text-2xl font-black text-foreground leading-none">
              {formatValue(card.value, card.format)}
            </span>
            {card.sparkData.length > 2 && (
              <ChartContainer config={sparkConfig} className="h-[28px] w-[56px] !aspect-auto">
                <AreaChart data={card.sparkData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary) / 0.1)"
                    strokeWidth={1.5}
                    dot={false}
                  />
                </AreaChart>
              </ChartContainer>
            )}
          </div>
          {card.delta !== null && (
            <div className={`flex items-center gap-1 text-xs font-medium ${card.delta >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              {card.delta >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {card.delta >= 0 ? '+' : ''}{card.delta.toFixed(1)}% vs anterior
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
