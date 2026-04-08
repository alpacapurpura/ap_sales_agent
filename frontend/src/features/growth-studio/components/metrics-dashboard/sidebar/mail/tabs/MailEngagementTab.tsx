'use client';

import { Loader2 } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Line,
  LineChart,
  Cell,
  Pie,
  PieChart,
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';

interface MailEngagementTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const ENGAGEMENT_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))'];
const ENGAGEMENT_METRICS = ['unique_opens', 'unique_clicks', 'forwards'];
const ENGAGEMENT_LABELS: Record<string, string> = {
  unique_opens: 'Aperturas',
  unique_clicks: 'Clics',
  forwards: 'Reenvíos',
};

export function MailEngagementTab({ data, isLoading }: MailEngagementTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const ctorKpi = data.kpis.find(k => k.metricName === 'click_to_open_rate');
  const clickRateKpi = data.kpis.find(k => k.metricName === 'click_rate');
  const forwardsTotal = data.timeSeries
    .find(s => s.metricName === 'forwards')
    ?.dataPoints.reduce((sum, p) => sum + p.value, 0) ?? 0;

  // Stacked bar data
  const seriesMap = new Map<string, Record<string, string | number>>();
  for (const metric of ENGAGEMENT_METRICS) {
    const ts = data.timeSeries.find(s => s.metricName === metric);
    if (!ts) continue;
    for (const dp of ts.dataPoints) {
      const entry = seriesMap.get(dp.date) ?? ({ date: dp.date } as Record<string, string | number>);
      entry[metric] = dp.value;
      seriesMap.set(dp.date, entry);
    }
  }
  const stackedData = Array.from(seriesMap.values())
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map(d => ({ ...d, date: String(d.date).slice(5) }));

  // Donut data
  const donutData = ENGAGEMENT_METRICS.map(metric => {
    const ts = data.timeSeries.find(s => s.metricName === metric);
    const total = ts?.dataPoints.reduce((sum, p) => sum + p.value, 0) ?? 0;
    return { name: ENGAGEMENT_LABELS[metric] ?? metric, value: total };
  }).filter(d => d.value > 0);

  // CTOR trend
  const ctorSeries = data.timeSeries.find(ts => ts.metricName === 'click_to_open_rate');
  const ctorTrend = ctorSeries?.dataPoints.map(p => ({ date: p.date.slice(5), value: p.value })) ?? [];

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <ChartSection slug="kpis-engagement">
        <div className="grid grid-cols-3 gap-3">
          {ctorKpi && (
            <div className="rounded-lg border bg-card p-4 space-y-1">
              <p className="text-xs text-muted-foreground">CTOR</p>
              <p className="text-2xl font-semibold tabular-nums">{ctorKpi.currentValue.toFixed(1)}%</p>
              {ctorKpi.benchmark && (
                <BenchmarkBadge value={ctorKpi.currentValue} benchmark={ctorKpi.benchmark} higherIsBetter={ctorKpi.higherIsBetter} />
              )}
            </div>
          )}
          {clickRateKpi && (
            <div className="rounded-lg border bg-card p-4 space-y-1">
              <p className="text-xs text-muted-foreground">Click Rate</p>
              <p className="text-2xl font-semibold tabular-nums">{clickRateKpi.currentValue.toFixed(2)}%</p>
              {clickRateKpi.benchmark && (
                <BenchmarkBadge value={clickRateKpi.currentValue} benchmark={clickRateKpi.benchmark} higherIsBetter={clickRateKpi.higherIsBetter} />
              )}
            </div>
          )}
          <div className="rounded-lg border bg-card p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Reenvíos</p>
            <p className="text-2xl font-semibold tabular-nums">{forwardsTotal.toLocaleString('en-US')}</p>
          </div>
        </div>
      </ChartSection>

      {/* Stacked Bar */}
      {stackedData.length > 0 && (
        <ChartSection slug="engagement-diario">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Desglose de Engagement Diario"
              description="Distribución diaria de aperturas, clics y reenvíos."
            />
            <ChartContainer
              config={{
                unique_opens: { label: 'Aperturas', color: ENGAGEMENT_COLORS[0] },
                unique_clicks: { label: 'Clics', color: ENGAGEMENT_COLORS[1] },
                forwards: { label: 'Reenvíos', color: ENGAGEMENT_COLORS[2] },
              }}
              className="h-[280px] w-full"
            >
              <BarChart data={stackedData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                {ENGAGEMENT_METRICS.map((metric, i) => (
                  <Bar
                    key={metric}
                    dataKey={metric}
                    stackId="engagement"
                    fill={ENGAGEMENT_COLORS[i]}
                    radius={i === ENGAGEMENT_METRICS.length - 1 ? [2, 2, 0, 0] : undefined}
                  />
                ))}
              </BarChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      {/* Donut */}
      {donutData.length > 0 && (
        <ChartSection slug="distribucion-engagement">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Distribución del Engagement"
              description="Proporción de cada tipo de interacción. Reenvíos indican contenido altamente compartible."
            />
            <div className="flex items-center gap-6">
              <ChartContainer config={{}} className="h-[200px] w-[200px] !aspect-auto">
                <PieChart>
                  <Pie data={donutData} innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                    {donutData.map((_, i) => (<Cell key={i} fill={ENGAGEMENT_COLORS[i % ENGAGEMENT_COLORS.length]} />))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ChartContainer>
              <div className="space-y-2">
                {donutData.map((d, i) => {
                  const total = donutData.reduce((s, e) => s + e.value, 0);
                  const pct = total > 0 ? ((d.value / total) * 100).toFixed(1) : '0.0';
                  return (
                    <div key={d.name} className="flex items-center gap-2 text-sm">
                      <span className="h-3 w-3 rounded-sm shrink-0" style={{ backgroundColor: ENGAGEMENT_COLORS[i % ENGAGEMENT_COLORS.length] }} />
                      <span className="text-muted-foreground">{d.name}</span>
                      <span className="font-medium tabular-nums ml-auto">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </ChartSection>
      )}

      {/* CTOR Trend */}
      {ctorTrend.length > 2 && (
        <ChartSection slug="tendencia-ctor">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Tendencia CTOR"
              description="CTOR mide calidad del contenido después de la apertura. >15% es bueno."
            />
            <ChartContainer
              config={{ value: { label: 'CTOR', color: 'hsl(var(--chart-3))' } }}
              className="h-[200px] w-full"
            >
              <LineChart data={ctorTrend}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" unit="%" />
                <RechartsTooltip />
                <Line type="monotone" dataKey="value" stroke="var(--color-value)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
    </div>
  );
}
