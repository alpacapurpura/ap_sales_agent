'use client';

import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import {
  Bar,
  ComposedChart,
  CartesianGrid,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { cn } from '@/lib/utils';
import { ChartContainer } from '@/components/ui/chart';
import { MetricInfoPopover } from '@/components/shared/MetricInfoPopover';
import { useMailDashboard } from '../../../../../hooks/useMailDashboard';
import { formatMetricValue } from '../../../../../utils/format-metric-value';
import { ChartSection } from '../../shared/ChartSection';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import type { MetaAdsPeriod, MetricKpiData } from '../../../../../types/metrics';
import type { EmailDashboardData, CampaignsVsAutomations } from '../../../../../types/mail-types';

interface MailPanoramaTabProps {
  period: MetaAdsPeriod;
}

// KPI definitions for the panorama overview
const PANORAMA_KPIS = [
  {
    metricName: 'emails_sent',
    description: 'Total de emails enviados en el periodo seleccionado.',
  },
  {
    metricName: 'open_rate',
    description: 'Porcentaje de emails abiertos sobre entregados. Mide calidad de subject lines.',
    formula: 'Abiertos / Entregados x 100',
  },
  {
    metricName: 'click_rate',
    description: 'Porcentaje de destinatarios que hicieron clic en al menos un enlace.',
    formula: 'Clics / Entregados x 100',
  },
  {
    metricName: 'click_to_open_rate',
    description: 'Porcentaje de personas que hicieron clic entre quienes abrieron. Mide calidad del contenido.',
    formula: 'Clics / Abiertos x 100',
  },
  {
    metricName: 'deliverability_rate',
    description: 'Porcentaje de emails entregados exitosamente. Menos del 95% indica problemas.',
    formula: 'Entregados / Enviados x 100',
  },
  {
    metricName: 'active_subscribers',
    description: 'Suscriptores activos en tu lista. Crecimiento neto del periodo.',
  },
];

// Industry benchmarks for comparison
const BENCHMARKS: Record<string, { value: number; label: string }> = {
  open_rate: { value: 21.5, label: 'Open Rate' },
  click_rate: { value: 2.3, label: 'Click Rate' },
  click_to_open_rate: { value: 10.5, label: 'CTOR' },
  unsubscribe_rate: { value: 0.1, label: 'Tasa de Baja' },
};

// Funnel step colors
const FUNNEL_COLORS = [
  'bg-blue-500',
  'bg-indigo-500',
  'bg-violet-500',
  'bg-purple-500',
  'bg-red-500',
];

export function MailPanoramaTab({ period }: MailPanoramaTabProps) {
  const { data, isLoading } = useMailDashboard(period);

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
        No hay datos disponibles para este periodo.
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto">
      {/* Section 1: KPI Cards */}
      <ChartSection slug="kpis">
        <KpiRow data={data} />
      </ChartSection>

      {/* Section 2: Volume vs Engagement + Funnel */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartSection slug="volumen-vs-engagement">
          <VolumeEngagementChart data={data} />
        </ChartSection>

        <ChartSection slug="embudo-email">
          <EmailFunnel data={data} />
        </ChartSection>
      </div>

      {/* Section 3: Benchmark Comparison + Campaigns vs Automations */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartSection slug="performance-vs-industria">
          <BenchmarkComparison data={data} />
        </ChartSection>

        {data.campaignsVsAutomations && (
          <ChartSection slug="campanas-vs-automatizaciones">
            <CampaignsVsAutomationsTable comparison={data.campaignsVsAutomations} />
          </ChartSection>
        )}
      </div>

      {/* Section 4: Recent Campaigns */}
      {(data.bestCampaign || data.worstCampaign) && (
        <ChartSection slug="campanas-recientes">
          <RecentCampaigns data={data} />
        </ChartSection>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiRow({ data }: { data: EmailDashboardData }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {PANORAMA_KPIS.map(config => {
        const kpi = data.kpis.find(k => k.metricName === config.metricName);
        if (!kpi) return null;

        const formattedValue = formatMetricValue(kpi.currentValue, kpi.unit, {
          currency: kpi.currency,
          percentDecimals: 1,
        });

        const isPositive =
          kpi.deltaPct != null &&
          (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);

        return (
          <div
            key={kpi.metricName}
            className="rounded-lg border bg-card p-3.5 space-y-1"
          >
            <MetricInfoPopover
              displayName={kpi.displayName}
              description={config.description}
              formula={config.formula}
              benchmark={
                kpi.benchmark
                  ? { value: kpi.benchmark.median }
                  : undefined
              }
            >
              <span className="text-[11px] text-muted-foreground">
                {kpi.displayName}
              </span>
            </MetricInfoPopover>

            <p className="text-xl font-semibold tabular-nums">{formattedValue}</p>

            {kpi.deltaPct != null && (
              <div className="flex items-center gap-1">
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 text-[11px] font-medium',
                    isPositive ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {kpi.unit === 'percentage'
                    ? `${Math.abs(kpi.deltaAbsolute ?? 0).toFixed(1)}pp`
                    : `${Math.abs(kpi.deltaPct).toFixed(0)}%`}
                  <span className="text-muted-foreground font-normal"> vs anterior</span>
                </span>
              </div>
            )}

            {kpi.benchmark && (
              <p className="text-[10px] text-muted-foreground/60">
                Benchmark: {kpi.benchmark.median}
                {kpi.unit === 'percentage' ? '%' : ''}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

function VolumeEngagementChart({ data }: { data: EmailDashboardData }) {
  const sentSeries = data.timeSeries.find(ts => ts.metricName === 'emails_sent');
  const openRateSeries = data.timeSeries.find(ts => ts.metricName === 'open_rate');

  const compositeData =
    sentSeries?.dataPoints.map(sp => {
      const openRate = openRateSeries?.dataPoints.find(op => op.date === sp.date);
      return {
        date: sp.date.slice(5),
        emails_sent: sp.value,
        open_rate: openRate?.value ?? 0,
      };
    }) ?? [];

  if (compositeData.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-5">
        <p className="text-sm text-muted-foreground">Sin datos de volumen disponibles.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Volumen vs Engagement"
        description="Compara envios (barras) con tasa de apertura (linea). Open rate estable al subir volumen = buena segmentacion."
      />
      <p className="text-[11px] text-muted-foreground -mt-1">
        Emails enviados (barras) vs Open Rate (linea) por semana
      </p>
      <ChartContainer
        config={{
          emails_sent: { label: 'Enviados', color: 'hsl(217, 91%, 60%)' },
          open_rate: { label: 'Open Rate', color: 'hsl(38, 92%, 50%)' },
        }}
        className="h-[220px] w-full"
      >
        <ComposedChart data={compositeData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="date" className="text-xs" />
          <YAxis yAxisId="left" className="text-xs" />
          <YAxis yAxisId="right" orientation="right" className="text-xs" unit="%" />
          <RechartsTooltip />
          <Bar
            yAxisId="left"
            dataKey="emails_sent"
            fill="var(--color-emails_sent)"
            radius={[3, 3, 0, 0]}
            opacity={0.7}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="open_rate"
            stroke="var(--color-open_rate)"
            strokeWidth={2.5}
            dot={{ r: 3.5, fill: 'var(--color-open_rate)' }}
          />
        </ComposedChart>
      </ChartContainer>
      <div className="flex gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-sm bg-blue-500" />
          Emails enviados
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          Open Rate
        </div>
      </div>
    </div>
  );
}

function EmailFunnel({ data }: { data: EmailDashboardData }) {
  const funnelSteps = data.funnel;

  if (funnelSteps.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-5">
        <p className="text-sm text-muted-foreground">Sin datos de embudo disponibles.</p>
      </div>
    );
  }

  const maxValue = Math.max(...funnelSteps.map(s => s.value), 1);

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Embudo de Email"
        description="Conversion desde envio hasta click. Cada paso muestra cuantos destinatarios avanzan."
      />
      <p className="text-[11px] text-muted-foreground -mt-1">
        Conversión desde envío hasta click (últimos {data.period})
      </p>
      <div className="space-y-2 pt-2">
        {funnelSteps.map((step, i) => {
          const widthPct = Math.max((step.value / maxValue) * 100, 5);
          return (
            <div key={step.metricName} className="flex items-center gap-3">
              <span className="w-[80px] text-right text-xs text-muted-foreground shrink-0">
                {step.label}
              </span>
              <div className="relative flex-1 h-8">
                <div
                  className={cn(
                    'h-full rounded-md flex items-center px-3',
                    FUNNEL_COLORS[i % FUNNEL_COLORS.length],
                  )}
                  style={{ width: `${widthPct}%` }}
                >
                  <span className="text-xs font-semibold text-white whitespace-nowrap">
                    {step.value.toLocaleString('en-US')}
                  </span>
                </div>
              </div>
              <span className="w-[55px] text-xs text-muted-foreground shrink-0">
                {step.conversionRate != null && i > 0
                  ? `${step.conversionRate.toFixed(1)}%`
                  : ''}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BenchmarkComparison({ data }: { data: EmailDashboardData }) {
  const entries = Object.entries(BENCHMARKS).map(([metricName, bench]) => {
    const kpi = data.kpis.find(k => k.metricName === metricName);
    return {
      metricName,
      label: bench.label,
      benchmarkValue: bench.value,
      yourValue: kpi?.currentValue ?? 0,
      higherIsBetter: kpi?.higherIsBetter ?? true,
    };
  });

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Tu Performance vs Industria"
        description="Comparación con promedios globales de email marketing. Verde = superando al benchmark."
      />
      <div className="grid grid-cols-2 gap-3 pt-1">
        {entries.map(entry => {
          const maxVal = Math.max(entry.yourValue, entry.benchmarkValue, 1);
          const yourPct = (entry.yourValue / maxVal) * 100;
          const benchPct = (entry.benchmarkValue / maxVal) * 100;
          const isAboveBenchmark = entry.higherIsBetter
            ? entry.yourValue >= entry.benchmarkValue
            : entry.yourValue <= entry.benchmarkValue;

          return (
            <div
              key={entry.metricName}
              className="rounded-md bg-muted/30 border border-border/50 p-3 space-y-2"
            >
              <p className="text-[11px] text-muted-foreground">{entry.label}</p>
              <div className="relative h-1.5 rounded-full bg-muted">
                <div
                  className={cn(
                    'h-full rounded-full',
                    isAboveBenchmark ? 'bg-emerald-500' : 'bg-red-500',
                  )}
                  style={{ width: `${Math.min(yourPct, 100)}%` }}
                />
                <div
                  className="absolute top-[-3px] h-[12px] w-[2px] bg-amber-500"
                  style={{ left: `${Math.min(benchPct, 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span
                  className={cn(
                    'font-semibold',
                    isAboveBenchmark ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {entry.yourValue.toFixed(1)}% (tú)
                </span>
                <span className="text-muted-foreground/60">
                  {entry.benchmarkValue}% (industria)
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CampaignsVsAutomationsTable({
  comparison,
}: {
  comparison: CampaignsVsAutomations;
}) {
  const rows = [
    {
      label: 'Enviados',
      campaigns: comparison.campaignsSent.toLocaleString('en-US'),
      automations: comparison.automationsSent.toLocaleString('en-US'),
      automationsBetter: comparison.automationsSent > comparison.campaignsSent,
    },
    {
      label: 'Open Rate',
      campaigns: `${comparison.campaignsOpenRate.toFixed(1)}%`,
      automations: `${comparison.automationsOpenRate.toFixed(1)}%`,
      automationsBetter: comparison.automationsOpenRate > comparison.campaignsOpenRate,
    },
    {
      label: 'Click Rate',
      campaigns: `${comparison.campaignsClickRate.toFixed(1)}%`,
      automations: `${comparison.automationsClickRate.toFixed(1)}%`,
      automationsBetter: comparison.automationsClickRate > comparison.campaignsClickRate,
    },
    {
      label: 'CTOR',
      campaigns: `${comparison.campaignsCtor.toFixed(1)}%`,
      automations: `${comparison.automationsCtor.toFixed(1)}%`,
      automationsBetter: comparison.automationsCtor > comparison.campaignsCtor,
    },
    {
      label: 'Bajas',
      campaigns: comparison.campaignsUnsubs.toLocaleString('en-US'),
      automations: comparison.automationsUnsubs.toLocaleString('en-US'),
      automationsBetter: comparison.automationsUnsubs < comparison.campaignsUnsubs,
    },
  ];

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Campañas vs Automatizaciones"
        description="Compara rendimiento entre envíos manuales y secuencias automatizadas."
      />
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[11px] text-muted-foreground border-b">
            <th className="text-left py-2 font-medium">Métrica</th>
            <th className="text-center py-2 font-medium">Campañas</th>
            <th className="text-center py-2 font-medium">Automatizaciones</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.label} className="border-b border-border/30">
              <td className="py-2.5 text-xs text-muted-foreground">{row.label}</td>
              <td className="py-2.5 text-center font-semibold text-xs">
                {row.campaigns}
              </td>
              <td
                className={cn(
                  'py-2.5 text-center font-semibold text-xs',
                  row.automationsBetter && 'text-emerald-600',
                )}
              >
                {row.automations}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Insight */}
      {comparison.automationsOpenRate > comparison.campaignsOpenRate && (
        <div className="rounded-md border-l-[3px] border-emerald-500 bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-emerald-600">Insight:</span>{' '}
            Las automatizaciones tienen{' '}
            {(
              ((comparison.automationsOpenRate - comparison.campaignsOpenRate) /
                comparison.campaignsOpenRate) *
              100
            ).toFixed(0)}
            % más engagement que las campañas manuales.
          </p>
        </div>
      )}
    </div>
  );
}

function RecentCampaigns({ data }: { data: EmailDashboardData }) {
  const campaigns = [data.bestCampaign, data.worstCampaign].filter(
    (c): c is NonNullable<typeof c> => c != null,
  );

  if (campaigns.length === 0) return null;

  const TYPE_STYLES: Record<string, string> = {
    newsletter: 'bg-neutral-500/10 text-neutral-400',
    lanzamiento: 'bg-violet-500/10 text-violet-400',
    promocion: 'bg-amber-500/10 text-amber-400',
    contenido: 'bg-blue-500/10 text-blue-400',
    reengagement: 'bg-red-500/10 text-red-400',
  };

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <ChartInfoTooltip
            title="Campañas Recientes"
            description="Resumen de las campañas más recientes. Ver tab Campañas para detalle completo."
          />
        </div>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[11px] text-muted-foreground border-b">
            <th className="text-left py-2 font-medium" style={{ width: '35%' }}>
              Campaña
            </th>
            <th className="text-center py-2 font-medium">Tipo</th>
            <th className="text-center py-2 font-medium">Enviados</th>
            <th className="text-center py-2 font-medium">Apertura</th>
            <th className="text-center py-2 font-medium">CTOR</th>
          </tr>
        </thead>
        <tbody>
          {campaigns.map((campaign, idx) => {
            const typeStyle =
              TYPE_STYLES[campaign.campaignType] ?? TYPE_STYLES.newsletter;
            const isAboveAvgOpen = campaign.openRate > 21.5;

            return (
              <tr
                key={`${campaign.campaignName}-${idx}`}
                className="border-b border-border/30 hover:bg-muted/30"
              >
                <td className="py-2.5 font-medium text-xs">
                  {campaign.campaignName}
                </td>
                <td className="py-2.5 text-center">
                  <span
                    className={cn(
                      'inline-block rounded-full px-2 py-0.5 text-[11px] font-medium',
                      typeStyle,
                    )}
                  >
                    {campaign.campaignType}
                  </span>
                </td>
                <td className="py-2.5 text-center text-xs tabular-nums">
                  {campaign.sentCount.toLocaleString('en-US')}
                </td>
                <td
                  className={cn(
                    'py-2.5 text-center text-xs font-semibold tabular-nums',
                    isAboveAvgOpen ? 'text-emerald-600' : 'text-amber-600',
                  )}
                >
                  {campaign.openRate.toFixed(1)}%
                </td>
                <td
                  className={cn(
                    'py-2.5 text-center text-xs font-semibold tabular-nums',
                    campaign.clickToOpenRate > 10.5
                      ? 'text-emerald-600'
                      : 'text-amber-600',
                  )}
                >
                  {campaign.clickToOpenRate.toFixed(1)}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
