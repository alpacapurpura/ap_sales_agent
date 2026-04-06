'use client';

import { Loader2 } from 'lucide-react';
import { Bar, ComposedChart, CartesianGrid, Line, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { MailHeroKpiGrid } from '../MailHeroKpiGrid';
import { MetaAdsMiniFunnel } from '../../meta-ads/MetaAdsMiniFunnel';
import { MailListGrowthIndicator } from '../MailListGrowthIndicator';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';

interface MailOverviewTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function MailOverviewTab({ data, isLoading }: MailOverviewTabProps) {
  if (isLoading) {
    return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  }
  if (!data) {
    return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;
  }

  const sentSeries = data.timeSeries.find(ts => ts.metricName === 'emails_sent');
  const openRateSeries = data.timeSeries.find(ts => ts.metricName === 'open_rate');

  const compositeData = sentSeries?.dataPoints.map(sp => {
    const openRate = openRateSeries?.dataPoints.find(op => op.date === sp.date);
    return { date: sp.date.slice(5), emails_sent: sp.value, open_rate: openRate?.value ?? 0 };
  }) ?? [];

  return (
    <div className="space-y-8">
      <MailHeroKpiGrid kpis={data.kpis} timeSeries={data.timeSeries} />
      {compositeData.length > 0 && (
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Volumen vs Engagement"
            description="Compara envíos (barras) con tasa de apertura (línea). Open rate estable al subir volumen = buena segmentación."
          />
          <ChartContainer
            config={{
              emails_sent: { label: 'Enviados', color: 'hsl(var(--chart-1))' },
              open_rate: { label: 'Open Rate', color: 'hsl(var(--chart-2))' },
            }}
            className="h-[250px] w-full"
          >
            <ComposedChart data={compositeData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis yAxisId="left" className="text-xs" />
              <YAxis yAxisId="right" orientation="right" className="text-xs" unit="%" />
              <RechartsTooltip />
              <Bar yAxisId="left" dataKey="emails_sent" fill="var(--color-emails_sent)" radius={[2, 2, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="open_rate" stroke="var(--color-open_rate)" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ChartContainer>
        </div>
      )}
      <MetaAdsMiniFunnel steps={data.funnel.steps} />
      <MailListGrowthIndicator kpis={data.kpis} />
    </div>
  );
}
