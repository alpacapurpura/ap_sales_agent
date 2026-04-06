'use client';

import { Loader2 } from 'lucide-react';
import {
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { MetricInfoCard } from '../../../channel-widgets/KpiTooltip';
import { ChartInfoTooltip } from '../../ig-organic/ChartInfoTooltip';
import type { ChannelDashboardData } from '../../../../../types/metrics';

interface YtEngagementTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function YtEngagementTab({ data, isLoading }: YtEngagementTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const engagementMetrics = ['comments', 'shares', 'engagement'];
  const engagementSeries = data.timeSeries.filter(ts => engagementMetrics.includes(ts.metricName));

  // Merge all engagement metrics by date
  const dateMap = new Map<string, Record<string, string | number>>();
  for (const series of engagementSeries) {
    for (const point of series.dataPoints) {
      const key = point.date.slice(5);
      const existing = dateMap.get(key) ?? { date: key };
      existing[series.metricName] = point.value;
      dateMap.set(key, existing);
    }
  }
  const chartData = Array.from(dateMap.values());

  // Card/End screen CTR KPIs
  const cardCtrKpi = data.kpis.find(k => k.metricName === 'card_click_rate');
  const endScreenCtrKpi = data.kpis.find(k => k.metricName === 'end_screen_click_rate');

  return (
    <div className="space-y-8">
      {/* CTR KPI Cards */}
      {(cardCtrKpi || endScreenCtrKpi) && (
        <div className="grid grid-cols-2 gap-4">
          {cardCtrKpi && (
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <MetricInfoCard metricName="card_click_rate">
                <p className="text-xs text-muted-foreground">{cardCtrKpi.displayName}</p>
              </MetricInfoCard>
              <p className="text-2xl font-semibold tabular-nums">
                {cardCtrKpi.currentValue.toFixed(1)}%
              </p>
              {cardCtrKpi.benchmark && (
                <BenchmarkBadge
                  value={cardCtrKpi.currentValue}
                  benchmark={cardCtrKpi.benchmark}
                  higherIsBetter={cardCtrKpi.higherIsBetter}
                />
              )}
            </div>
          )}
          {endScreenCtrKpi && (
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <MetricInfoCard metricName="end_screen_click_rate">
                <p className="text-xs text-muted-foreground">{endScreenCtrKpi.displayName}</p>
              </MetricInfoCard>
              <p className="text-2xl font-semibold tabular-nums">
                {endScreenCtrKpi.currentValue.toFixed(1)}%
              </p>
              {endScreenCtrKpi.benchmark && (
                <BenchmarkBadge
                  value={endScreenCtrKpi.currentValue}
                  benchmark={endScreenCtrKpi.benchmark}
                  higherIsBetter={endScreenCtrKpi.higherIsBetter}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Engagement trend chart */}
      {chartData.length > 0 && (
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Tendencia de Engagement"
            description="Comentarios, shares y engagement total a lo largo del tiempo. Un engagement constante indica contenido que conecta con tu audiencia."
          />
          <ChartContainer
            config={{
              comments: { label: 'Comentarios', color: 'hsl(var(--chart-1))' },
              shares: { label: 'Compartidos', color: 'hsl(var(--chart-2))' },
              engagement: { label: 'Engagement Total', color: 'hsl(var(--chart-3))' },
            }}
            className="h-[250px] w-full"
          >
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip />
              <Line type="monotone" dataKey="comments" stroke="var(--color-comments)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="shares" stroke="var(--color-shares)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="engagement" stroke="var(--color-engagement)" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartContainer>
        </div>
      )}
    </div>
  );
}
