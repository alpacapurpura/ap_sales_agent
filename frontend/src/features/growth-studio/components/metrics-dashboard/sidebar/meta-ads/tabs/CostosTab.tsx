'use client';

import { Loader2 } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import { ChartSection } from '../../shared/ChartSection';
import type { ChannelDashboardData, MetricKpiData, CampaignPerformanceData } from '../../../../../types/metrics';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';

interface CostosTabProps {
  data: ChannelDashboardData | undefined;
  campaignData: CampaignPerformanceData | undefined;
  isLoading: boolean;
}

const COST_METRICS = ['CPC', 'CPM', 'CPL', 'CPA'];

/** Metrics that require Meta Pixel to report meaningful data. When value is 0, show "--" placeholder. */
const PIXEL_DEPENDENT_METRICS = new Set(['ROAS', 'CPA', 'CPL', 'conversions']);

function isPixelPlaceholder(metricName: string, value: number): boolean {
  return PIXEL_DEPENDENT_METRICS.has(metricName) && value === 0;
}

const COST_TOOLTIPS: Record<string, string> = {
  CPC: 'CPC = Cuánto pagas cada vez que alguien hace clic en tu anuncio. Menor es mejor.',
  CPM: 'CPM = Cuánto pagas por cada 1,000 veces que se muestra tu anuncio.',
  CPL: 'CPL = Cuánto cuesta cada contacto interesado que generas. Menor es mejor.',
  CPA: 'CPA = Cuánto pagas por cada resultado (venta o acción). Menor es mejor.',
};

export function CostosTab({ data, campaignData, isLoading }: CostosTabProps) {
  const { currency: tenantCurrency } = useTenantLocale();

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

  const costKpis = COST_METRICS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  // Build cost evolution data from timeSeries
  const costSeries = COST_METRICS.map(name =>
    data.timeSeries.find(ts => ts.metricName === name),
  ).filter(Boolean);

  const costChartData: Record<string, number | string>[] = [];
  const firstSeries = costSeries[0];
  if (firstSeries) {
    for (const point of firstSeries.dataPoints) {
      const entry: Record<string, number | string> = { date: point.date.slice(5) };
      for (const s of costSeries) {
        if (!s) continue;
        const p = s.dataPoints.find(dp => dp.date === point.date);
        entry[s.metricName] = p?.value ?? 0;
      }
      costChartData.push(entry);
    }
  }

  // CPA by campaign from campaignData
  const campaignsWithCpa = campaignData?.campaigns
    .filter(c => c.metrics.cpa != null && c.metrics.cpa > 0)
    .sort((a, b) => (a.metrics.cpa ?? 0) - (b.metrics.cpa ?? 0)) ?? [];
  const maxCpa = campaignsWithCpa.length > 0
    ? Math.max(...campaignsWithCpa.map(c => c.metrics.cpa ?? 0))
    : 1;

  return (
    <div className="space-y-6">
      {/* 4 Cost KPIs with benchmarks */}
      <ChartSection slug="kpis-costos">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {costKpis.map(kpi => (
            <div
              key={kpi.metricName}
              className="space-y-1.5 rounded-lg border bg-card p-4"
              title={COST_TOOLTIPS[kpi.metricName] ?? ''}
            >
              <p className="text-xs text-muted-foreground">{kpi.displayName}</p>
              <p className="text-2xl font-semibold tabular-nums">
                {isPixelPlaceholder(kpi.metricName, kpi.currentValue) ? (
                  <span title="Requiere Meta Pixel configurado">--</span>
                ) : (
                  formatMoney(kpi.currentValue, kpi.currency || tenantCurrency)
                )}
              </p>
              {kpi.benchmark && (
                <BenchmarkBadge
                  value={kpi.currentValue}
                  benchmark={kpi.benchmark}
                  higherIsBetter={kpi.higherIsBetter}
                />
              )}
            </div>
          ))}
        </div>
      </ChartSection>

      {/* Cost Evolution Chart */}
      {costChartData.length > 0 && (
        <ChartSection slug="tendencia-costos">
          <div className="space-y-2">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Evolución de costos
            </h3>
            <ChartContainer
              config={{
                CPC: { label: 'CPC', color: 'hsl(var(--chart-1))' },
                CPM: { label: 'CPM', color: 'hsl(var(--chart-3))' },
                CPL: { label: 'CPL', color: 'hsl(var(--chart-4))' },
              }}
              className="h-[250px] w-full"
            >
              <LineChart data={costChartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Line type="monotone" dataKey="CPC" stroke="var(--color-CPC)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="CPM" stroke="var(--color-CPM)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="CPL" stroke="var(--color-CPL)" strokeWidth={2} dot={false} />
                {(() => {
                  const cpcBenchmark = costKpis.find(k => k.metricName === 'CPC')?.benchmark;
                  return cpcBenchmark ? (
                    <ReferenceLine
                      y={cpcBenchmark.median}
                      stroke="var(--color-CPC)"
                      strokeDasharray="4 6"
                      strokeOpacity={0.3}
                      label={{ value: 'Prom. CPC', position: 'right', fontSize: 9, fill: 'var(--color-CPC)' }}
                    />
                  ) : null;
                })()}
              </LineChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      {/* CPA by Campaign comparison */}
      {campaignsWithCpa.length > 0 && (
        <ChartSection slug="desglose-costos-campana">
          <div className="space-y-2">
            <h3
              className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
              title="Compara el costo por resultado de cada campaña."
            >
              CPA por campaña
            </h3>
            <div className="rounded-lg border bg-card p-4 space-y-2.5">
              {campaignsWithCpa.map(camp => {
                const pct = ((camp.metrics.cpa ?? 0) / maxCpa) * 100;
                const isHigh = camp.health === 'critical';
                return (
                  <div key={camp.externalId} className="flex items-center gap-3">
                    <span
                      className={cn(
                        'text-xs w-36 truncate',
                        isHigh ? 'text-destructive' : 'text-muted-foreground',
                      )}
                    >
                      {camp.name}
                    </span>
                    <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                      <div
                        className={cn(
                          'h-full rounded-full flex items-center justify-end pr-2 text-[10px] font-semibold',
                          isHigh ? 'bg-destructive/50 text-destructive' : 'bg-emerald-500/40',
                        )}
                        style={{ width: `${Math.max(pct, 8)}%` }}
                      >
                        {formatMoney(camp.metrics.cpa ?? 0, campaignData?.currency || tenantCurrency)}
                      </div>
                    </div>
                  </div>
                );
              })}
              {(() => {
                const cpaBenchmark = costKpis.find(k => k.metricName === 'CPA')?.benchmark;
                if (!cpaBenchmark || maxCpa === 0) return null;
                const benchPct = (cpaBenchmark.median / maxCpa) * 100;
                return (
                  <div className="flex items-center gap-3 pt-1 border-t border-dashed border-muted-foreground/20">
                    <span className="text-[10px] text-muted-foreground w-36 text-right">
                      Prom. industria
                    </span>
                    <div className="flex-1 relative h-5">
                      <div
                        className="absolute top-0 h-full border-l-2 border-dashed border-muted-foreground/40"
                        style={{ left: `${Math.min(benchPct, 100)}%` }}
                      />
                      <span
                        className="absolute top-0.5 text-[9px] text-muted-foreground"
                        style={{ left: `${Math.min(benchPct + 1, 85)}%` }}
                      >
                        {formatMoney(cpaBenchmark.median, campaignData?.currency || tenantCurrency)}
                      </span>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        </ChartSection>
      )}
    </div>
  );
}
