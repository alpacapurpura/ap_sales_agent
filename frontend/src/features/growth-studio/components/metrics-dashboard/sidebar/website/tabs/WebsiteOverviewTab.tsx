'use client';

import { Loader2 } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { HeroKpiGrid } from '../../shared/HeroKpiGrid';
import { MetaAdsMiniFunnel } from '../../meta-ads/MetaAdsMiniFunnel';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';
import type { WebsiteData } from '../types';

const HERO_METRICS = ['sessions', 'engagementRate', 'conversions'] as const;

interface WebsiteOverviewTabProps {
  data: WebsiteData | undefined;
  isLoading: boolean;
}

export function WebsiteOverviewTab({ data, isLoading }: WebsiteOverviewTabProps) {
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

  const sessionsSeries = data.timeSeries.find(ts => ts.metricName === 'sessions');
  const chartData =
    sessionsSeries?.dataPoints.map(p => ({
      date: p.date.slice(5),
      sessions: p.value,
    })) ?? [];

  return (
    <div className="space-y-8">
      <ChartSection slug="kpis">
        <HeroKpiGrid
          kpis={data.kpis}
          timeSeries={data.timeSeries}
          heroMetrics={[...HERO_METRICS]}
          gradientPrefix="web-overview"
        />
      </ChartSection>

      {chartData.length > 0 && (
        <ChartSection slug="sesiones-tendencia">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Tendencia de Sesiones"
              description="Evolución de sesiones en el tiempo. Una sesión agrupa las interacciones de un usuario en tu sitio. Crecimiento sostenido indica buena tracción."
            />
            <ChartContainer
              config={{
                sessions: { label: 'Sesiones', color: 'hsl(var(--chart-1))' },
              }}
              className="h-[250px] w-full"
            >
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="web-sessions-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-sessions)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="var(--color-sessions)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Area
                  type="monotone"
                  dataKey="sessions"
                  stroke="var(--color-sessions)"
                  strokeWidth={2}
                  fill="url(#web-sessions-grad)"
                />
              </AreaChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      <ChartSection slug="embudo">
        <MetaAdsMiniFunnel steps={data.funnel.steps} />
      </ChartSection>
    </div>
  );
}
