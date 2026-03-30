'use client';

import { useMemo } from 'react';
import { Area, AreaChart } from 'recharts';
import { ChartContainer } from '@/components/ui/chart';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { StageTimeSeries } from '../../../types/metrics';

interface AttractionScorecardsProps {
  timeSeries: StageTimeSeries | undefined;
  totalReach: number;
  totalVisitors: number;
  totalLeads: number;
  leadConvRate: number;
}

interface ScorecardData {
  label: string;
  value: number;
  format: 'number' | 'percent' | 'money';
  delta: number | null;
  sparkData: { v: number }[];
}

function formatValue(value: number, format: 'number' | 'percent' | 'money'): string {
  if (format === 'percent') return `${value.toFixed(1)}%`;
  if (format === 'money') return `$${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })}`;
  return value.toLocaleString('es-ES');
}

function computeDelta(current: number, previous: number | null): number | null {
  if (previous === null || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

export function AttractionScorecards({
  timeSeries,
  totalReach,
  totalVisitors,
  totalLeads,
  leadConvRate,
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
    const visitorDelta = computeDelta(currTotal, prevTotal);

    return [
      {
        label: 'Alcance',
        value: totalReach,
        format: 'number',
        delta: null, // no time-series for reach yet
        sparkData: [],
      },
      {
        label: 'Visitantes',
        value: totalVisitors,
        format: 'number',
        delta: visitorDelta,
        sparkData: dailyTotals,
      },
      {
        label: 'Conv. %',
        value: leadConvRate,
        format: 'percent',
        delta: null,
        sparkData: [],
      },
      {
        label: 'Leads',
        value: totalLeads,
        format: 'number',
        delta: null,
        sparkData: [],
      },
    ];
  }, [timeSeries, totalReach, totalVisitors, totalLeads, leadConvRate]);

  const sparkConfig = { v: { color: 'hsl(var(--primary))' } };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-card border border-border rounded-lg p-4 flex flex-col gap-1"
        >
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
            {card.label}
          </span>
          <div className="flex items-end justify-between gap-2">
            <span className="text-3xl font-black text-foreground leading-none">
              {formatValue(card.value, card.format)}
            </span>
            {card.sparkData.length > 2 && (
              <ChartContainer config={sparkConfig} className="h-[30px] w-[60px] !aspect-auto">
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
              {card.delta >= 0 ? '+' : ''}{card.delta.toFixed(1)}% vs periodo anterior
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
