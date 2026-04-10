'use client';

import {
  Bar,
  Cell,
  ComposedChart,
  CartesianGrid,
  LabelList,
  Line,
  ReferenceLine,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { ChartInfoTooltip } from '../shared/ChartInfoTooltip';
import type { MetricTimeSeries } from '../../../../types/metrics';

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

interface InversionChartProps {
  timeSeries: MetricTimeSeries[];
}

// ---------------------------------------------------------------------------
// Constants — labels, colors, formatters
// ---------------------------------------------------------------------------

const LABELS: Record<string, string> = {
  spend: 'Inversión',
  conversions: 'Resultados',
  roas: 'ROAS',
};

const COLORS: Record<string, string> = {
  spend: 'hsl(var(--chart-1))',
  conversions: 'hsl(var(--chart-2))',
  roas: 'hsl(45 93% 47%)',
};

const BAR_COLOR_PROFIT = 'hsl(142 71% 45%)';
const BAR_COLOR_LOSS = 'hsl(0 84% 60%)';
const BAR_COLOR_MUTED = 'hsl(var(--muted))';

function getBarColor(roas: number | null | undefined): string {
  if (roas == null) return BAR_COLOR_MUTED;
  return roas >= 1 ? BAR_COLOR_PROFIT : BAR_COLOR_LOSS;
}

// Spanish month names
const MONTHS_ES_SHORT = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun',
  'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
];

const MONTHS_ES_LONG = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

function formatDateEs(isoDate: string): string {
  const parts = isoDate.split('-');
  if (parts.length < 3) return isoDate;
  const day = parseInt(parts[2], 10);
  const month = parseInt(parts[1], 10) - 1;
  if (Number.isNaN(day) || Number.isNaN(month)) return isoDate;
  return `${day} ${MONTHS_ES_SHORT[month] ?? ''}`.trim();
}

function formatDateEsLong(isoDate: string): string {
  const parts = isoDate.split('-');
  if (parts.length < 3) return isoDate;
  const day = parseInt(parts[2], 10);
  const month = parseInt(parts[1], 10) - 1;
  if (Number.isNaN(day) || Number.isNaN(month)) return isoDate;
  return `${day} de ${MONTHS_ES_LONG[month] ?? ''}`.trim();
}

// ---------------------------------------------------------------------------
// Tooltip — exported for unit testing
// ---------------------------------------------------------------------------

export interface TooltipEntry {
  dataKey: string;
  value: number;
  color: string;
  payload?: Record<string, unknown>;
}

interface InversionTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
  currency: string;
}

export function InversionTooltip({ active, payload, currency }: InversionTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  // Hide entirely when every series is zero for this point
  const allZero = payload.every(entry => !entry.value);
  if (allZero) return null;

  const firstPayload = payload[0]?.payload;
  const isoDate = typeof firstPayload?.isoDate === 'string'
    ? (firstPayload.isoDate as string)
    : undefined;
  const dateLabel = isoDate ? formatDateEsLong(isoDate) : '';

  const visible = payload.filter(entry => entry.value !== 0 && entry.value != null);
  if (visible.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 shadow-lg">
      {dateLabel && (
        <p className="mb-1.5 text-xs font-medium capitalize">{dateLabel}</p>
      )}
      <div className="space-y-1">
        {visible.map(entry => {
          const key = entry.dataKey;
          const label = LABELS[key] ?? key;
          const color = COLORS[key] ?? entry.color;
          const formatted = formatTooltipValue(key, entry.value, currency);
          return (
            <div
              key={key}
              className="flex items-center justify-between gap-4 text-xs"
            >
              <div className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 shrink-0 rounded-sm"
                  style={{ backgroundColor: color }}
                />
                <span className="text-muted-foreground">{label}</span>
              </div>
              <span className="font-medium tabular-nums text-foreground">
                {formatted}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatTooltipValue(key: string, value: number, currency: string): string {
  if (key === 'spend') return formatMoney(value, currency);
  if (key === 'roas') return `${value.toFixed(2)}x`;
  if (key === 'conversions') return value.toLocaleString('es-PE');
  return value.toLocaleString('es-PE');
}

// ---------------------------------------------------------------------------
// Main chart component
// ---------------------------------------------------------------------------

interface CompositePoint {
  isoDate: string;
  date: string;
  spend: number;
  conversions: number;
  roas: number | null;
}

export function InversionChart({ timeSeries }: InversionChartProps) {
  const { currency: tenantCurrency } = useTenantLocale();

  const compositeData = buildCompositeData(timeSeries);

  if (compositeData.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-5">
        <ChartInfoTooltip
          title="Inversión y Retorno"
          description="Barras = inversión diaria coloreadas por ROAS (verde = rentable, rojo = bajo break-even). Línea amarilla = ROAS vs meta (break-even en 1.0x)."
        />
        <p className="mt-3 text-sm text-muted-foreground">
          Sin actividad publicitaria para mostrar en este periodo.
        </p>
      </div>
    );
  }

  // Narrative calculations
  const totalSpend = compositeData.reduce((s, d) => s + d.spend, 0);
  const daysCount = compositeData.length;
  const roasValues = compositeData
    .map(d => d.roas)
    .filter((r): r is number => r != null);
  const avgRoas = roasValues.length > 0
    ? roasValues.reduce((s, r) => s + r, 0) / roasValues.length
    : null;
  const bestDay = compositeData.reduce<CompositePoint | null>((best, d) => {
    if (d.roas == null) return best;
    if (best == null || d.roas > (best.roas ?? -Infinity)) return d;
    return best;
  }, null);

  const narrativeWarn = avgRoas != null && avgRoas < 1;
  const narrativeClass = narrativeWarn
    ? 'text-red-500'
    : 'text-muted-foreground';

  // Max spend (for data labels on outlier days)
  const maxSpend = Math.max(...compositeData.map(d => d.spend));

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Inversión y Retorno"
        description="Barras = inversión diaria coloreadas por ROAS (verde = rentable, rojo = bajo break-even). Línea amarilla = ROAS vs meta (break-even en 1.0x)."
      />

      <p className={cn('text-xs', narrativeClass)}>
        Invertiste{' '}
        <span className="font-semibold text-foreground">
          {formatMoney(totalSpend, tenantCurrency)}
        </span>{' '}
        en {daysCount} {daysCount === 1 ? 'día' : 'días'}
        {avgRoas != null && (
          <>
            {' · '}
            ROAS promedio{' '}
            <span
              className={cn(
                'font-semibold',
                narrativeWarn ? 'text-red-500' : 'text-emerald-500',
              )}
            >
              {avgRoas.toFixed(2)}x
            </span>
          </>
        )}
        {bestDay && (
          <>
            {' · '}
            Mejor día:{' '}
            <span className="font-semibold text-foreground">
              {formatDateEs(bestDay.isoDate)}
            </span>
          </>
        )}
        {narrativeWarn && (
          <span className="ml-1 italic">— por debajo de break-even</span>
        )}
      </p>

      <ChartContainer
        config={{
          spend: { label: 'Inversión', color: 'hsl(var(--chart-1))' },
          conversions: { label: 'Resultados', color: 'hsl(var(--chart-2))' },
          roas: { label: 'ROAS', color: 'hsl(45 93% 47%)' },
        }}
        className="h-[320px] w-full"
      >
        <ComposedChart data={compositeData} barSize={24}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted/40" />
          <XAxis
            dataKey="isoDate"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: string) => formatDateEs(v)}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) =>
              formatMoney(v, tenantCurrency, { compact: true })
            }
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => `${v.toFixed(1)}x`}
          />
          <RechartsTooltip
            content={<InversionTooltip currency={tenantCurrency} />}
          />
          <ReferenceLine
            yAxisId="right"
            y={1}
            stroke="hsl(var(--muted-foreground))"
            strokeDasharray="4 4"
            label={{
              value: 'Break-even',
              position: 'right',
              fill: 'hsl(var(--muted-foreground))',
              fontSize: 10,
            }}
          />
          <Bar yAxisId="left" dataKey="spend" radius={[3, 3, 0, 0]}>
            {compositeData.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={getBarColor(entry.roas)} />
            ))}
            <LabelList
              dataKey="spend"
              position="top"
              className="fill-foreground text-[10px] font-medium"
              formatter={(v: number) =>
                v === maxSpend ? formatMoney(v, tenantCurrency, { compact: true }) : ''
              }
            />
          </Bar>
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="roas"
            stroke={COLORS.roas}
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="conversions"
            stroke={COLORS.conversions}
            strokeWidth={1.5}
            strokeDasharray="6 4"
            dot={false}
          />
        </ComposedChart>
      </ChartContainer>

      <div className="flex flex-wrap gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span
            className="h-2 w-2 rounded-sm"
            style={{ backgroundColor: BAR_COLOR_PROFIT }}
          />
          Rentable (ROAS ≥ 1)
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span
            className="h-2 w-2 rounded-sm"
            style={{ backgroundColor: BAR_COLOR_LOSS }}
          />
          Bajo break-even
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span
            className="h-0.5 w-4 rounded-sm"
            style={{ backgroundColor: COLORS.roas }}
          />
          ROAS
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span
            className="h-0.5 w-4 rounded-sm border-t border-dashed"
            style={{ borderColor: COLORS.conversions }}
          />
          Resultados
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data transformation
// ---------------------------------------------------------------------------

function buildCompositeData(timeSeries: MetricTimeSeries[]): CompositePoint[] {
  const spendSeries = timeSeries.find(ts => ts.metricName === 'spend');
  const convSeries = timeSeries.find(ts => ts.metricName === 'conversions');
  const roasSeries = timeSeries.find(ts => ts.metricName === 'ROAS');

  if (!spendSeries) return [];

  const raw: CompositePoint[] = spendSeries.dataPoints.map(sp => {
    const conv = convSeries?.dataPoints.find(c => c.date === sp.date);
    const roas = roasSeries?.dataPoints.find(r => r.date === sp.date);
    return {
      isoDate: sp.date,
      date: formatDateEs(sp.date),
      spend: sp.value,
      conversions: conv?.value ?? 0,
      roas: roas?.value ?? null,
    };
  });

  // Filter out zero-activity days
  return raw.filter(d => d.spend > 0 || d.conversions > 0);
}
