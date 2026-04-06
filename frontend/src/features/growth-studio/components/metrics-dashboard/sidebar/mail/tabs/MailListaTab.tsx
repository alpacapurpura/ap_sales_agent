'use client';

import { Loader2 } from 'lucide-react';
import {
  Bar,
  ComposedChart,
  CartesianGrid,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { cn } from '@/lib/utils';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';

interface MailListaTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function MailListaTab({ data, isLoading }: MailListaTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const activeSubsKpi = data.kpis.find(k => k.metricName === 'active_subscribers');
  const newSubsTotal = data.timeSeries.find(s => s.metricName === 'new_subscribers')?.dataPoints.reduce((sum, p) => sum + p.value, 0) ?? 0;
  const unsubsTotal = data.timeSeries.find(s => s.metricName === 'unsubscribes')?.dataPoints.reduce((sum, p) => sum + p.value, 0) ?? 0;
  const churnRatio = newSubsTotal > 0 ? (unsubsTotal / newSubsTotal) * 100 : 0;

  const formConversionsKpi = data.kpis.find(k => k.metricName === 'form_conversions');
  const formConvRateKpi = data.kpis.find(k => k.metricName === 'form_conversion_rate');

  // Composed chart: new subs (green bars) + unsubs (red bars negative) + active (line right axis)
  const newSubsSeries = data.timeSeries.find(ts => ts.metricName === 'new_subscribers');
  const unsubsSeries = data.timeSeries.find(ts => ts.metricName === 'unsubscribes');
  const activeSubsSeries = data.timeSeries.find(ts => ts.metricName === 'active_subscribers');

  const allDates = new Set<string>();
  [newSubsSeries, unsubsSeries, activeSubsSeries].forEach(ts => {
    ts?.dataPoints.forEach(p => allDates.add(p.date));
  });

  const compositeData = Array.from(allDates)
    .sort()
    .map(date => ({
      date: date.slice(5),
      new_subscribers: newSubsSeries?.dataPoints.find(p => p.date === date)?.value ?? 0,
      unsubscribes: -(unsubsSeries?.dataPoints.find(p => p.date === date)?.value ?? 0),
      active_subscribers: activeSubsSeries?.dataPoints.find(p => p.date === date)?.value ?? 0,
    }));

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border bg-card p-4 space-y-1">
          <p className="text-xs text-muted-foreground">Suscriptores Activos</p>
          <p className="text-2xl font-semibold tabular-nums">
            {(activeSubsKpi?.currentValue ?? 0).toLocaleString('en-US')}
          </p>
          {activeSubsKpi?.deltaPct != null && (
            <p className={cn('text-xs font-medium', activeSubsKpi.deltaPct >= 0 ? 'text-emerald-600' : 'text-red-600')}>
              {activeSubsKpi.deltaPct >= 0 ? '+' : ''}{activeSubsKpi.deltaPct.toFixed(1)}% vs anterior
            </p>
          )}
        </div>
        <div className="rounded-lg border bg-card p-4 space-y-1">
          <p className="text-xs text-muted-foreground">Nuevos (periodo)</p>
          <p className="text-2xl font-semibold tabular-nums text-emerald-600">
            +{newSubsTotal.toLocaleString('en-US')}
          </p>
        </div>
      </div>

      {/* Growth Chart */}
      {compositeData.length > 0 && (
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Crecimiento de Lista"
            description="Lista saludable crece 2-5% mensual. Barras verdes = nuevos, rojas = desuscripciones, línea = total activos."
          />
          <ChartContainer
            config={{
              new_subscribers: { label: 'Nuevos', color: 'hsl(142 76% 36%)' },
              unsubscribes: { label: 'Desuscripciones', color: 'hsl(0 72% 51%)' },
              active_subscribers: { label: 'Activos', color: 'hsl(var(--chart-2))' },
            }}
            className="h-[280px] w-full"
          >
            <ComposedChart data={compositeData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis yAxisId="left" className="text-xs" />
              <YAxis yAxisId="right" orientation="right" className="text-xs" />
              <RechartsTooltip />
              <Bar yAxisId="left" dataKey="new_subscribers" fill="var(--color-new_subscribers)" radius={[2, 2, 0, 0]} />
              <Bar yAxisId="left" dataKey="unsubscribes" fill="var(--color-unsubscribes)" radius={[2, 2, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="active_subscribers" stroke="var(--color-active_subscribers)" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ChartContainer>
        </div>
      )}

      {/* Churn Ratio */}
      <div className="space-y-2">
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Ratio de Churn
        </h4>
        <div className={cn(
          'rounded-lg border p-4 flex items-center gap-4',
          churnRatio < 50 ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900' :
          churnRatio < 100 ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900' :
          'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900',
        )}>
          <span className={cn(
            'text-3xl font-bold tabular-nums',
            churnRatio < 50 ? 'text-emerald-600' : churnRatio < 100 ? 'text-amber-600' : 'text-red-600',
          )}>
            {churnRatio.toFixed(0)}%
          </span>
          <div>
            <p className="text-sm font-medium">
              {churnRatio < 50 ? 'Lista creciendo' : churnRatio < 100 ? 'Crecimiento lento' : 'Lista encogiendo'}
            </p>
            <p className="text-xs text-muted-foreground">
              {unsubsTotal} desuscripciones / {newSubsTotal} nuevos
            </p>
          </div>
        </div>
      </div>

      {/* Form Performance */}
      {formConversionsKpi && formConversionsKpi.currentValue > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Formularios
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border bg-card p-4 space-y-1">
              <p className="text-xs text-muted-foreground">Conversiones</p>
              <p className="text-2xl font-semibold tabular-nums">{formConversionsKpi.currentValue.toLocaleString('en-US')}</p>
            </div>
            {formConvRateKpi && (
              <div className="rounded-lg border bg-card p-4 space-y-1">
                <p className="text-xs text-muted-foreground">Tasa Conversión</p>
                <p className="text-2xl font-semibold tabular-nums">{formConvRateKpi.currentValue.toFixed(1)}%</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
