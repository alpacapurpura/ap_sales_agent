'use client';

import { Loader2 } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ComposedChart, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { MetaAdsHeroKpiGrid } from '../MetaAdsHeroKpiGrid';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import { ReachFrequencySection } from '../ReachFrequencySection';

interface OverviewTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function OverviewTab({ data, isLoading }: OverviewTabProps) {
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

  const spendSeries = data.timeSeries.find(ts => ts.metricName === 'spend');
  const convSeries = data.timeSeries.find(ts => ts.metricName === 'conversions');

  // Merge spend and conversions for composite chart
  const compositeData = spendSeries?.dataPoints.map(sp => {
    const conv = convSeries?.dataPoints.find(c => c.date === sp.date);
    return {
      date: sp.date.slice(5), // MM-DD
      spend: sp.value,
      conversions: conv?.value ?? 0,
    };
  }) ?? [];

  return (
    <div className="space-y-8">
      <MetaAdsHeroKpiGrid kpis={data.kpis} timeSeries={data.timeSeries} />

      {compositeData.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Inversión vs Conversiones</h3>
          <ChartContainer
            config={{
              spend: { label: 'Inversión', color: 'hsl(var(--chart-1))' },
              conversions: { label: 'Conversiones', color: 'hsl(var(--chart-2))' },
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

      <MetaAdsMiniFunnel steps={data.funnel.steps} />
      <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />
    </div>
  );
}
