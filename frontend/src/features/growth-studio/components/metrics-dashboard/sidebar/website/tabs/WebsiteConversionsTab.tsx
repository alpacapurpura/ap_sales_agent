'use client';

import { Loader2, ShoppingBag } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { MetaAdsMiniFunnel } from '../../meta-ads/MetaAdsMiniFunnel';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';
import type { WebsiteData } from '../types';

interface WebsiteConversionsTabProps {
  data: WebsiteData | undefined;
  isLoading: boolean;
}

export function WebsiteConversionsTab({ data, isLoading }: WebsiteConversionsTabProps) {
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

  // Compute conversion rate from KPIs
  const sessionsKpi = data.kpis.find(k => k.metricName === 'sessions');
  const conversionsKpi = data.kpis.find(k => k.metricName === 'conversions');
  const sessions = sessionsKpi?.currentValue ?? 0;
  const conversions = conversionsKpi?.currentValue ?? 0;
  const conversionRate = sessions > 0 ? (conversions / sessions) * 100 : 0;

  // Conversion rate trend from time series
  const conversionsSeries = data.timeSeries.find(ts => ts.metricName === 'conversions');
  const chartData =
    conversionsSeries?.dataPoints.map(p => ({
      date: p.date.slice(5),
      conversions: p.value,
    })) ?? [];

  return (
    <div className="space-y-8">
      {/* Conversion Rate KPI Card */}
      <ChartSection slug="tasa-conversion">
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Tasa de Conversión"
            description="Porcentaje de sesiones que resultan en una conversión (compra, suscripción, registro). Benchmark: e-commerce 1-3%, landing pages 5-15%, SaaS 3-7%."
          />
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-bold tabular-nums">
                {conversionRate.toFixed(2)}%
              </span>
              <span className="text-sm text-muted-foreground">
                {conversions.toLocaleString('en-US')} conversiones de{' '}
                {sessions.toLocaleString('en-US')} sesiones
              </span>
            </div>
          </div>
        </div>
      </ChartSection>

      {/* Conversions Trend Chart */}
      {chartData.length > 0 && (
        <ChartSection slug="tendencia-conversiones">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Tendencia de Conversiones"
              description="Evolución diaria de conversiones. Busca patrones: picos en días de campaña, caídas en fin de semana. Correlaciona con tu calendario de contenido."
            />
            <ChartContainer
              config={{
                conversions: { label: 'Conversiones', color: 'hsl(var(--chart-3))' },
              }}
              className="h-[250px] w-full"
            >
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="web-conv-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="0%"
                      stopColor="var(--color-conversions)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="100%"
                      stopColor="var(--color-conversions)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Area
                  type="monotone"
                  dataKey="conversions"
                  stroke="var(--color-conversions)"
                  strokeWidth={2}
                  fill="url(#web-conv-grad)"
                />
              </AreaChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      {/* Mini Funnel */}
      <ChartSection slug="embudo-conversion">
        <MetaAdsMiniFunnel steps={data.funnel.steps} />
      </ChartSection>

      {/* E-commerce Placeholder */}
      <ChartSection slug="ecommerce">
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Métricas de E-commerce"
            description="Ingresos, valor promedio de orden, tasa de abandono de carrito y más. Requiere conexión con tu plataforma de pagos."
          />
          <div className="rounded-lg border border-dashed p-8 text-center">
            <ShoppingBag className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">
              Conecta Shopify para ver métricas de e-commerce
            </p>
          </div>
        </div>
      </ChartSection>
    </div>
  );
}
