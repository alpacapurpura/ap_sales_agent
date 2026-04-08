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
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { MailDeliverabilityHealth } from '../MailDeliverabilityHealth';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';

interface MailEntregabilidadTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

function getSeverityColor(value: number, thresholds: { warning: number; critical: number }, lowerIsBetter: boolean): string {
  if (lowerIsBetter) {
    if (value >= thresholds.critical) return 'text-red-600';
    if (value >= thresholds.warning) return 'text-amber-600';
    return 'text-emerald-600';
  }
  if (value <= thresholds.critical) return 'text-red-600';
  if (value <= thresholds.warning) return 'text-amber-600';
  return 'text-emerald-600';
}

export function MailEntregabilidadTab({ data, isLoading }: MailEntregabilidadTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const bounceRateKpi = data.kpis.find(k => k.metricName === 'bounce_rate');
  const spamKpi = data.kpis.find(k => k.metricName === 'spam_reports');
  const unsubRateKpi = data.kpis.find(k => k.metricName === 'unsubscribe_rate');
  const emailsSent = data.kpis.find(k => k.metricName === 'emails_sent')?.currentValue ?? 0;
  const spamRate = emailsSent > 0 && spamKpi ? (spamKpi.currentValue / emailsSent) * 100 : 0;

  // Bounce breakdown
  const hardTotal = data.timeSeries.find(s => s.metricName === 'hard_bounces')?.dataPoints.reduce((s, p) => s + p.value, 0) ?? 0;
  const softTotal = data.timeSeries.find(s => s.metricName === 'soft_bounces')?.dataPoints.reduce((s, p) => s + p.value, 0) ?? 0;
  const bounceBreakdown = [
    { name: 'Duros', value: hardTotal },
    { name: 'Suaves', value: softTotal },
  ];

  // Trend data
  const bounceRateSeries = data.timeSeries.find(ts => ts.metricName === 'bounce_rate');
  const unsubRateSeries = data.timeSeries.find(ts => ts.metricName === 'unsubscribe_rate');
  const trendMap = new Map<string, Record<string, string | number>>();
  for (const ts of [bounceRateSeries, unsubRateSeries].filter(Boolean)) {
    for (const dp of ts!.dataPoints) {
      const entry = trendMap.get(dp.date) ?? ({ date: dp.date } as Record<string, string | number>);
      entry[ts!.metricName] = dp.value;
      trendMap.set(dp.date, entry);
    }
  }
  const trendData = Array.from(trendMap.values())
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map(d => ({ ...d, date: String(d.date).slice(5) }));

  return (
    <div className="space-y-8">
      {/* Health Score */}
      <ChartSection slug="salud-entregabilidad">
        <MailDeliverabilityHealth kpis={data.kpis} />
      </ChartSection>

      {/* KPI Cards */}
      <ChartSection slug="kpis-entregabilidad">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border bg-card p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Bounce Rate</p>
            <p className={cn('text-2xl font-semibold tabular-nums', getSeverityColor(bounceRateKpi?.currentValue ?? 0, { warning: 2, critical: 5 }, true))}>
              {(bounceRateKpi?.currentValue ?? 0).toFixed(2)}%
            </p>
          </div>
          <div className="rounded-lg border bg-card p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Spam Reports</p>
            <p className={cn('text-2xl font-semibold tabular-nums', getSeverityColor(spamRate, { warning: 0.05, critical: 0.1 }, true))}>
              {(spamKpi?.currentValue ?? 0).toLocaleString('en-US')}
            </p>
            <p className="text-xs text-muted-foreground">{spamRate.toFixed(3)}%</p>
          </div>
          <div className="rounded-lg border bg-card p-4 space-y-1">
            <p className="text-xs text-muted-foreground">Desuscripción</p>
            <p className={cn('text-2xl font-semibold tabular-nums', getSeverityColor(unsubRateKpi?.currentValue ?? 0, { warning: 0.2, critical: 0.5 }, true))}>
              {(unsubRateKpi?.currentValue ?? 0).toFixed(2)}%
            </p>
          </div>
        </div>
      </ChartSection>

      {/* Bounce Breakdown */}
      {(hardTotal > 0 || softTotal > 0) && (
        <ChartSection slug="desglose-rebotes">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Desglose de Rebotes"
              description="Rebotes duros = direcciones inválidas (permanentes). Suaves = buzón lleno o temporales."
            />
            <ChartContainer
              config={{
                Duros: { label: 'Duros', color: 'hsl(var(--chart-1))' },
                Suaves: { label: 'Suaves', color: 'hsl(var(--chart-2))' },
              }}
              className="h-[120px] w-full"
            >
              <BarChart data={bounceBreakdown} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis type="number" className="text-xs" />
                <YAxis dataKey="name" type="category" className="text-xs" width={60} />
                <RechartsTooltip />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  <Bar dataKey="value" fill="hsl(var(--chart-1))" />
                </Bar>
              </BarChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      {/* Trend */}
      {trendData.length > 2 && (
        <ChartSection slug="tendencia-salud">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Tendencia de Salud"
              description="Evolución del bounce rate y desuscripción. Ambos deben mantenerse bajos."
            />
            <ChartContainer
              config={{
                bounce_rate: { label: 'Bounce Rate', color: 'hsl(var(--chart-1))' },
                unsubscribe_rate: { label: 'Desuscripción', color: 'hsl(var(--chart-3))' },
              }}
              className="h-[200px] w-full"
            >
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" unit="%" />
                <RechartsTooltip />
                <Line type="monotone" dataKey="bounce_rate" stroke="var(--color-bounce_rate)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="unsubscribe_rate" stroke="var(--color-unsubscribe_rate)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
    </div>
  );
}
