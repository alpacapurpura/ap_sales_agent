'use client';

import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import {
  Bar,
  ComposedChart,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { cn } from '@/lib/utils';
import { ChartContainer } from '@/components/ui/chart';
import { MetricInfoPopover } from '@/components/shared/MetricInfoPopover';
import { useMailGrowth } from '../../../../../hooks/useMailDashboard';
import { formatMetricValue } from '../../../../../utils/format-metric-value';
import { ChartSection } from '../../shared/ChartSection';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import type { MetaAdsPeriod, MetricKpiData } from '../../../../../types/metrics';
import type {
  EmailGrowthData,
  EmailSourcePerformance,
  EngagementDecay,
} from '../../../../../types/mail-types';

interface MailCrecimientoTabProps {
  period: MetaAdsPeriod;
}

// KPI definitions
const GROWTH_KPIS = [
  {
    metricName: 'active_subscribers',
    description: 'Total de suscriptores activos en tu lista al final del periodo.',
  },
  {
    metricName: 'new_subscribers',
    description: 'Nuevos suscriptores adquiridos durante el periodo seleccionado.',
  },
  {
    metricName: 'unsubscribes',
    description: 'Suscriptores que se dieron de baja en el periodo.',
  },
  {
    metricName: 'list_growth_rate',
    description:
      'Tasa de crecimiento neto de la lista. Un 2-5% mensual es saludable.',
    formula: '(Nuevos - Bajas) / Total anterior x 100',
  },
];

export function MailCrecimientoTab({ period }: MailCrecimientoTabProps) {
  const { data, isLoading } = useMailGrowth(period);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
          <TrendingUp className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin datos de crecimiento</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Los datos de crecimiento se generarán cuando tengas historial de suscripciones.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto">
      {/* Section 1: KPI Cards */}
      <ChartSection slug="kpis-crecimiento">
        <KpiRow data={data} />
      </ChartSection>

      {/* Section 2: Growth Chart */}
      <ChartSection slug="grafico-crecimiento">
        <GrowthChart data={data} />
      </ChartSection>

      {/* Section 3: Sources + Retention */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {data.sources.length > 0 && (
          <ChartSection slug="fuentes-suscripcion">
            <SourcesChart sources={data.sources} />
          </ChartSection>
        )}

        {data.retentionCurve.length > 0 && (
          <ChartSection slug="curva-retencion">
            <RetentionCurve retention={data.retentionCurve} />
          </ChartSection>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiRow({ data }: { data: EmailGrowthData }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {GROWTH_KPIS.map(config => {
        const kpi = data.kpis.find(k => k.metricName === config.metricName);
        if (!kpi) return null;

        return (
          <KpiCard
            key={kpi.metricName}
            kpi={kpi}
            description={config.description}
            formula={config.formula}
          />
        );
      })}
    </div>
  );
}

function KpiCard({
  kpi,
  description,
  formula,
}: {
  kpi: MetricKpiData;
  description: string;
  formula?: string;
}) {
  const formattedValue = formatMetricValue(kpi.currentValue, kpi.unit, {
    currency: kpi.currency,
    percentDecimals: 1,
  });

  const isPositive =
    kpi.deltaPct != null &&
    (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);

  return (
    <div className="rounded-lg border bg-card p-3.5 space-y-1">
      <MetricInfoPopover
        displayName={kpi.displayName}
        description={description}
        formula={formula}
        benchmark={
          kpi.benchmark ? { value: kpi.benchmark.median } : undefined
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
    </div>
  );
}

// #8: Spanish month names for date formatting
const MONTHS_ES = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun',
  'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
];

function formatDateEs(isoDate: string): string {
  const [, month, day] = isoDate.split('-');
  return `${parseInt(day, 10)} ${MONTHS_ES[parseInt(month, 10) - 1]}`;
}

function formatDateEsLong(isoDate: string): string {
  const [, month, day] = isoDate.split('-');
  const monthNames = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
  ];
  return `${parseInt(day, 10)} de ${monthNames[parseInt(month, 10) - 1]}`;
}

// #1-5: Custom tooltip with Spanish labels, formatted numbers, date header
interface TooltipEntry {
  dataKey: string;
  value: number;
  color: string;
  payload?: Record<string, unknown>;
}

function GrowthTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  const LABELS: Record<string, string> = {
    new_subscribers: 'Nuevos suscriptores',
    unsubscribes: 'Bajas',
    active_subscribers: 'Total activos',
  };

  const COLORS: Record<string, string> = {
    new_subscribers: 'rgb(34, 197, 94)',
    unsubscribes: 'rgb(239, 68, 68)',
    active_subscribers: 'rgb(59, 130, 246)',
  };

  const originalDate = payload[0]?.payload?.isoDate as string | undefined;
  const dateLabel = originalDate ? formatDateEsLong(originalDate) : (label ?? '');

  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 shadow-lg">
      {/* #3: Date header */}
      <p className="mb-1.5 text-xs font-medium capitalize">{dateLabel}</p>
      <div className="space-y-1">
        {payload.map(entry => {
          const absValue = Math.abs(entry.value);
          // #5: Hide metrics with value 0
          if (absValue === 0) return null;
          const key = entry.dataKey;
          return (
            <div key={key} className="flex items-center justify-between gap-4 text-xs">
              {/* #4: Color bullet + black text */}
              <div className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 shrink-0 rounded-sm"
                  style={{ backgroundColor: COLORS[key] ?? entry.color }}
                />
                <span className="text-muted-foreground">{LABELS[key] ?? key}</span>
              </div>
              {/* #2: Formatted number */}
              <span className="font-medium tabular-nums">
                {absValue.toLocaleString('es-PE')}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function GrowthChart({ data }: { data: EmailGrowthData }) {
  const newSubsSeries = data.timeSeries.find(
    ts => ts.metricName === 'new_subscribers',
  );
  const unsubsSeries = data.timeSeries.find(
    ts => ts.metricName === 'unsubscribes',
  );
  const activeSeries = data.timeSeries.find(
    ts => ts.metricName === 'active_subscribers',
  );

  const dateMap = new Map<
    string,
    { date: string; isoDate: string; new_subscribers: number; unsubscribes: number; active_subscribers: number }
  >();

  const getEntry = (isoDate: string) =>
    dateMap.get(isoDate) ?? {
      date: formatDateEs(isoDate),
      isoDate,
      new_subscribers: 0,
      unsubscribes: 0,
      active_subscribers: 0,
    };

  for (const dp of newSubsSeries?.dataPoints ?? []) {
    const entry = getEntry(dp.date);
    entry.new_subscribers = dp.value;
    dateMap.set(dp.date, entry);
  }
  for (const dp of unsubsSeries?.dataPoints ?? []) {
    const entry = getEntry(dp.date);
    entry.unsubscribes = -Math.abs(dp.value);
    dateMap.set(dp.date, entry);
  }
  for (const dp of activeSeries?.dataPoints ?? []) {
    const entry = getEntry(dp.date);
    entry.active_subscribers = dp.value;
    dateMap.set(dp.date, entry);
  }

  // #13: Only days with activity (new_subscribers > 0 or unsubscribes != 0)
  const compositeData = Array.from(dateMap.values())
    .filter(d => d.new_subscribers > 0 || d.unsubscribes < 0)
    .sort((a, b) => a.isoDate.localeCompare(b.isoDate));

  if (compositeData.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          Sin datos de crecimiento para graficar.
        </p>
      </div>
    );
  }

  // Attach active_subscribers from the full dateMap for filtered days
  for (const d of compositeData) {
    const full = dateMap.get(d.isoDate);
    if (full) d.active_subscribers = full.active_subscribers;
  }

  // #6: Right Y-axis domain — tight range so the line variation is visible
  const activeValues = compositeData.map(d => d.active_subscribers).filter(v => v > 0);
  const activeMin = Math.min(...activeValues);
  const activeMax = Math.max(...activeValues);
  const activeMargin = Math.max(Math.ceil((activeMax - activeMin) * 0.3), 5);
  const rightDomain: [number, number] = [
    Math.max(0, activeMin - activeMargin),
    activeMax + activeMargin,
  ];

  // #12: Narrative summary
  const totalNew = compositeData.reduce((s, d) => s + d.new_subscribers, 0);
  const totalUnsubs = compositeData.reduce((s, d) => s + Math.abs(d.unsubscribes), 0);
  const net = totalNew - totalUnsubs;
  const narrativeClass = net >= 0 ? 'text-emerald-500' : 'text-red-500';
  const narrativeSign = net >= 0 ? '+' : '';

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Evolución de la Lista"
        description="Barras verdes = nuevos suscriptores, barras rojas = bajas. La línea muestra el total activo."
      />
      {/* #12: Narrative line */}
      <p className="text-xs text-muted-foreground">
        Tu lista creció{' '}
        <span className={cn('font-semibold', narrativeClass)}>
          {narrativeSign}{net}
        </span>
        {' '}neto: +{totalNew} nuevos, -{totalUnsubs} bajas
      </p>
      <ChartContainer
        config={{
          new_subscribers: {
            label: 'Nuevos suscriptores',
            color: 'hsl(142, 71%, 45%)',
          },
          unsubscribes: {
            label: 'Bajas',
            color: 'hsl(0, 84%, 60%)',
          },
          active_subscribers: {
            label: 'Total activos',
            color: 'hsl(217, 91%, 60%)',
          },
        }}
        className="h-[280px] w-full"
      >
        <ComposedChart data={compositeData} barSize={24}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted/40" />
          {/* #8: Date format "16 mar" */}
          <XAxis
            dataKey="date"
            className="text-xs"
            tick={{ fontSize: 11 }}
          />
          {/* #7: Left Y-axis with absolute values */}
          <YAxis
            yAxisId="left"
            className="text-xs"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => `${Math.abs(v)}`}
          />
          {/* #6: Right Y-axis with tight domain */}
          <YAxis
            yAxisId="right"
            orientation="right"
            className="text-xs"
            tick={{ fontSize: 11 }}
            domain={rightDomain}
            tickFormatter={(v: number) => v.toLocaleString('es-PE')}
          />
          {/* #1-5: Custom tooltip */}
          <RechartsTooltip content={<GrowthTooltip />} />
          {/* Green bars UP from 0, red bars DOWN from 0 — no stacking */}
          <Bar
            yAxisId="left"
            dataKey="new_subscribers"
            fill="var(--color-new_subscribers)"
            radius={[3, 3, 0, 0]}
          >
            <LabelList
              dataKey="new_subscribers"
              position="top"
              className="fill-emerald-400 text-[10px] font-medium"
              formatter={(v: number) => (v > 0 ? v : '')}
            />
          </Bar>
          <Bar
            yAxisId="left"
            dataKey="unsubscribes"
            fill="var(--color-unsubscribes)"
            radius={[0, 0, 3, 3]}
          >
            <LabelList
              dataKey="unsubscribes"
              position="bottom"
              className="fill-red-400 text-[10px] font-medium"
              formatter={(v: number) => (v < 0 ? Math.abs(v) : '')}
            />
          </Bar>
          {/* #9: Line without dots */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="active_subscribers"
            stroke="var(--color-active_subscribers)"
            strokeWidth={2.5}
            dot={false}
          />
        </ComposedChart>
      </ChartContainer>
      <div className="flex gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-sm bg-emerald-500" />
          Nuevos suscriptores
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-sm bg-red-500" />
          Bajas
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-blue-500" />
          Total activos
        </div>
      </div>
    </div>
  );
}

function SourcesChart({ sources }: { sources: EmailSourcePerformance[] }) {
  const maxCount = Math.max(...sources.map(s => s.subscriberCount), 1);
  const sorted = [...sources].sort(
    (a, b) => b.subscriberCount - a.subscriberCount,
  );

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Fuentes de Suscripción"
        description="De dónde vienen los nuevos suscriptores y su tasa de conversión."
      />
      <div className="space-y-3 pt-1">
        {sorted.map(source => {
          const widthPct = Math.max(
            (source.subscriberCount / maxCount) * 100,
            5,
          );

          return (
            <div key={source.source} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium">{source.label}</span>
                <span className="text-muted-foreground tabular-nums">
                  {source.subscriberCount.toLocaleString('en-US')}{' '}
                  <span className="text-[10px]">({source.percentage.toFixed(0)}%)</span>
                </span>
              </div>
              <div className="relative h-6 rounded-md bg-muted/30 overflow-hidden">
                <div
                  className="h-full rounded-md bg-gradient-to-r from-blue-600 to-blue-400 flex items-center px-2.5"
                  style={{ width: `${widthPct}%` }}
                >
                  {widthPct > 20 && (
                    <span className="text-[10px] font-semibold text-white whitespace-nowrap">
                      Open: {source.openRate.toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RetentionCurve({ retention }: { retention: EngagementDecay[] }) {
  // Map retention data to bar chart format
  const barData = retention.map(r => ({
    label: r.periodLabel,
    retained: r.openRate,
  }));

  if (barData.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Curva de Retención"
        description="Porcentaje de suscriptores que siguen activos en cada hito temporal."
      />
      <ChartContainer
        config={{
          retained: { label: '% Retenidos', color: 'hsl(217, 91%, 60%)' },
        }}
        className="h-[200px] w-full"
      >
        <BarChart data={barData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="label" className="text-xs" />
          <YAxis className="text-xs" unit="%" />
          <RechartsTooltip />
          <Bar
            dataKey="retained"
            fill="var(--color-retained)"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ChartContainer>

      {/* Insight about retention */}
      {retention.length >= 2 && (
        <div className="rounded-md border-l-[3px] border-blue-500 bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-blue-600">Retención:</span>{' '}
            {retention[retention.length - 1].openRate.toFixed(0)}% de los
            suscriptores siguen activos a los{' '}
            {retention[retention.length - 1].periodLabel}.
          </p>
        </div>
      )}
    </div>
  );
}
