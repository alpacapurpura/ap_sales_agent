'use client';

import { Loader2, TrendingDown, TrendingUp } from 'lucide-react';
import { Bar, ComposedChart, CartesianGrid, Line, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import type { ChannelDashboardData, MetricKpiData } from '../../../../../types/metrics';

interface ResumenTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const RESUMEN_KPIS = ['spend', 'ROAS', 'conversions', 'CPA', 'CTR', 'reach'];

function formatKpiValue(value: number, unit: string, currency?: string): string {
  if (unit === 'currency') return formatMoney(value, currency || 'USD');
  if (unit === 'percentage') return `${value.toFixed(2)}%`;
  if (unit === 'ratio') return `${value.toFixed(2)}x`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString('en-US');
}

const KPI_TOOLTIPS: Record<string, string> = {
  spend: 'Total invertido en Meta Ads durante el periodo seleccionado.',
  ROAS: 'ROAS = Por cada $1 invertido, cuánto recuperas. Ej: 3.2x = ganas $3.20 por cada $1.',
  conversions: 'Total de resultados (ventas, leads, etc.) generados por todas tus campañas.',
  CPA: 'CPA = Costo por cada resultado obtenido. Menor es mejor.',
  CTR: 'CTR = % de personas que ven tu anuncio y hacen clic. Más alto es mejor.',
  reach: 'Personas únicas que vieron tus anuncios. No es una suma diaria.',
};

export function ResumenTab({ data, isLoading }: ResumenTabProps) {
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

  const kpis = RESUMEN_KPIS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  const spendSeries = data.timeSeries.find(ts => ts.metricName === 'spend');
  const convSeries = data.timeSeries.find(ts => ts.metricName === 'conversions');

  const compositeData = spendSeries?.dataPoints.map(sp => {
    const conv = convSeries?.dataPoints.find(c => c.date === sp.date);
    return {
      date: sp.date.slice(5),
      spend: sp.value,
      conversions: conv?.value ?? 0,
    };
  }) ?? [];

  return (
    <div className="space-y-6">
      {/* 6 KPI cards */}
      <div className="grid grid-cols-6 gap-2.5">
        {kpis.map(kpi => {
          const isPositive =
            kpi.deltaPct != null &&
            (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);
          return (
            <div
              key={kpi.metricName}
              className="rounded-lg border bg-card p-3 space-y-1"
              title={KPI_TOOLTIPS[kpi.metricName] ?? ''}
            >
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                {kpi.displayName}
              </p>
              <p className="text-xl font-bold tabular-nums">
                {formatKpiValue(kpi.currentValue, kpi.unit, kpi.currency)}
              </p>
              {kpi.deltaPct != null && (
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 text-[10px] font-medium',
                    isPositive ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {Math.abs(kpi.deltaPct).toFixed(1)}% vs ant.
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
          );
        })}
      </div>

      {/* 2-column: Chart + Funnel */}
      <div className="grid grid-cols-2 gap-4">
        {/* Spend vs Conversions chart */}
        {compositeData.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Inversión vs Resultados
            </h3>
            <ChartContainer
              config={{
                spend: { label: 'Inversión', color: 'hsl(var(--chart-1))' },
                conversions: { label: 'Resultados', color: 'hsl(var(--chart-2))' },
              }}
              className="h-[250px] w-full"
            >
              <ComposedChart data={compositeData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis yAxisId="left" className="text-xs" />
                <YAxis yAxisId="right" orientation="right" className="text-xs" />
                <RechartsTooltip />
                <Bar yAxisId="left" dataKey="spend" fill="var(--color-spend)" radius={[2, 2, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="conversions" stroke="var(--color-conversions)" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ChartContainer>
          </div>
        )}

        {/* Full Funnel */}
        <div className="space-y-2">
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Embudo de conversión
          </h3>
          <MetaAdsMiniFunnel steps={data.funnel.steps} />
        </div>
      </div>
    </div>
  );
}
