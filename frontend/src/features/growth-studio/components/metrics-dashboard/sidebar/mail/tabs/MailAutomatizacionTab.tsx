'use client';

import { Loader2 } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { MetaAdsMiniFunnel } from '../../meta-ads/MetaAdsMiniFunnel';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';

interface MailAutomatizacionTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function MailAutomatizacionTab({ data, isLoading }: MailAutomatizacionTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const completedKpi = data.kpis.find(k => k.metricName === 'automation_completed');
  const completionRateKpi = data.kpis.find(k => k.metricName === 'completion_rate');

  // Completion rate trend
  const completionSeries = data.timeSeries.find(ts => ts.metricName === 'completion_rate');
  const completionTrend = completionSeries?.dataPoints.map(p => ({ date: p.date.slice(5), value: p.value })) ?? [];

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border bg-card p-4 space-y-1">
          <p className="text-xs text-muted-foreground">Automatizaciones Completadas</p>
          <p className="text-2xl font-semibold tabular-nums">
            {(completedKpi?.currentValue ?? 0).toLocaleString('en-US')}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4 space-y-1">
          <p className="text-xs text-muted-foreground">Tasa de Completado</p>
          <p className="text-2xl font-semibold tabular-nums">
            {(completionRateKpi?.currentValue ?? 0).toFixed(1)}%
          </p>
          {completionRateKpi?.benchmark && (
            <BenchmarkBadge
              value={completionRateKpi.currentValue}
              benchmark={completionRateKpi.benchmark}
              higherIsBetter={completionRateKpi.higherIsBetter}
            />
          )}
        </div>
      </div>

      {/* Mini Funnel */}
      <div className="space-y-2">
        <ChartInfoTooltip
          title="Funnel de Automatización"
          description="Muestra cuántas personas completan tus secuencias de email. Una caída fuerte indica contenido poco relevante."
        />
        <MetaAdsMiniFunnel steps={data.funnel.steps} />
      </div>

      {/* Completion Rate Trend */}
      {completionTrend.length > 2 && (
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Tendencia Tasa de Completado"
            description="Porcentaje de suscriptores que completan la secuencia de automatización. >45% es bueno."
          />
          <ChartContainer
            config={{ value: { label: 'Completado', color: 'hsl(var(--chart-1))' } }}
            className="h-[200px] w-full"
          >
            <AreaChart data={completionTrend}>
              <defs>
                <linearGradient id="mail-completion-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-value)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--color-value)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" unit="%" />
              <RechartsTooltip />
              <Area type="monotone" dataKey="value" stroke="var(--color-value)" strokeWidth={2} fill="url(#mail-completion-grad)" />
            </AreaChart>
          </ChartContainer>
        </div>
      )}
    </div>
  );
}
