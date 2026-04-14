"use client";

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
} from "recharts";

import { ChartContainer } from "@/components/ui/chart";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { ChartInfoTooltip } from "../shared/ChartInfoTooltip";
import type { MetricTimeSeries } from "../../../../types/metrics";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export type InversionChartFilter = "all" | "offer" | "branding" | "unassigned";

export interface InversionChartProps {
  timeSeries: MetricTimeSeries[];
  /**
   * Active segmenter filter. Drives the narrative subtitle, the legend and
   * which data series are rendered. Defaults to `'all'` for backwards
   * compatibility.
   */
  filter?: InversionChartFilter;
  /**
   * When `filter === 'offer'`, the offer's user-visible name used in the
   * narrative subtitle (e.g. "Pack Verano 2026").
   */
  offerName?: string;
}

// ---------------------------------------------------------------------------
// Constants — labels, colors, formatters
// ---------------------------------------------------------------------------

const COLORS = {
  spend: "hsl(var(--chart-1))",
  conversions: "hsl(var(--chart-2))",
  roas: "hsl(45 93% 47%)",
} as const;

const BAR_COLOR_PROFIT = "hsl(142 71% 45%)";
const BAR_COLOR_LOSS = "hsl(0 84% 60%)";
const BAR_COLOR_MUTED = "hsl(var(--muted))";

// Thresholds for the bar/tooltip status chip:
// - ROAS >= 1  → "Rentable" (above break-even — every sol invested returned ≥ 1 sol)
// - 0 < ROAS < 1 → "Bajo break-even" (losing money)
// - ROAS == null AND we expected conversions → "Sin pixel" (attribution missing)
// - ROAS == null AND we did NOT expect conversions (branding / unassigned) → no chip
// We keep the threshold at exactly 1.0 because break-even is mathematically
// ROAS == 1 — anything above is profit, anything below is loss. This matches
// the horizontal ReferenceLine on the right axis.
function getBarColor(roas: number | null | undefined): string {
  if (roas == null) return BAR_COLOR_MUTED;
  return roas >= 1 ? BAR_COLOR_PROFIT : BAR_COLOR_LOSS;
}

// Spanish month names
const MONTHS_ES_SHORT = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
];

const MONTHS_ES_LONG = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

function formatDateEs(isoDate: string): string {
  const parts = isoDate.split("-");
  if (parts.length < 3) return isoDate;
  const day = parseInt(parts[2], 10);
  const month = parseInt(parts[1], 10) - 1;
  if (Number.isNaN(day) || Number.isNaN(month)) return isoDate;
  return `${day} ${MONTHS_ES_SHORT[month] ?? ""}`.trim();
}

function formatDateEsLong(isoDate: string): string {
  const parts = isoDate.split("-");
  if (parts.length < 3) return isoDate;
  const day = parseInt(parts[2], 10);
  const month = parseInt(parts[1], 10) - 1;
  if (Number.isNaN(day) || Number.isNaN(month)) return isoDate;
  return `${day} de ${MONTHS_ES_LONG[month] ?? ""}`.trim();
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

export type TooltipStatus = "profitable" | "below_break_even" | "no_pixel" | "none";

interface InversionTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
  currency: string;
  /**
   * User-visible label for the "Resultados" row (singular or singular+plural
   * are handled upstream — we render verbatim). Defaults to 'Resultados'.
   */
  resultsLabel?: string;
  /**
   * When true, the status chip is hidden entirely (branding / unassigned —
   * no attribution, no break-even concept).
   */
  hideStatusChip?: boolean;
  /**
   * When true, we expect the chart to render ROAS data — used to
   * distinguish "Sin pixel" (expected ROAS but null) from "no attribution
   * relevant" (branding / unassigned).
   */
  expectsRoas?: boolean;
}

function computeStatus(
  roas: number | null | undefined,
  conversions: number | null | undefined,
  expectsRoas: boolean,
): TooltipStatus {
  if (!expectsRoas) return "none";
  if (roas == null) {
    // No ROAS data and no conversions on a day we expected them → pixel off.
    if ((conversions ?? 0) === 0) return "no_pixel";
    return "none";
  }
  return roas >= 1 ? "profitable" : "below_break_even";
}

export function InversionTooltip({
  active,
  payload,
  currency,
  resultsLabel = "Resultados",
  hideStatusChip = false,
  expectsRoas = true,
}: InversionTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  // Hide entirely when every series is zero for this point
  const allZero = payload.every((entry) => !entry.value);
  if (allZero) return null;

  const firstPayload = payload[0]?.payload;
  const isoDate =
    typeof firstPayload?.isoDate === "string" ? (firstPayload.isoDate as string) : undefined;
  const dateLabel = isoDate ? formatDateEsLong(isoDate) : "";

  const visible = payload.filter((entry) => entry.value !== 0 && entry.value != null);
  if (visible.length === 0) return null;

  // Labels are driven by props so the chart can show "Leads", "Compras",
  // etc. when a specific offer is selected.
  const labelByKey: Record<string, string> = {
    spend: "Inversión",
    conversions: resultsLabel,
    roas: "ROAS",
  };

  // Compute status from the original payload (not filtered) so that a day
  // with spend > 0 but ROAS null (pixel off) still gets the chip.
  const roasEntry = payload.find((e) => e.dataKey === "roas");
  const conversionsEntry = payload.find((e) => e.dataKey === "conversions");
  const status = hideStatusChip
    ? "none"
    : computeStatus(roasEntry?.value ?? null, conversionsEntry?.value ?? null, expectsRoas);

  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 shadow-lg">
      {dateLabel && <p className="mb-1.5 text-xs font-medium capitalize">{dateLabel}</p>}
      <div className="space-y-1">
        {visible.map((entry) => {
          const key = entry.dataKey;
          const label = labelByKey[key] ?? key;
          const color = COLORS[key as keyof typeof COLORS] ?? entry.color;
          const formatted = formatTooltipValue(key, entry.value, currency);
          return (
            <div key={key} className="flex items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 shrink-0 rounded-sm" style={{ backgroundColor: color }} />
                <span className="text-muted-foreground">{label}</span>
              </div>
              <span className="font-medium tabular-nums text-foreground">{formatted}</span>
            </div>
          );
        })}
      </div>
      {status !== "none" && (
        <div className="mt-2 border-t border-border pt-1.5">
          <StatusChip status={status} />
        </div>
      )}
    </div>
  );
}

function StatusChip({ status }: { status: Exclude<TooltipStatus, "none"> }) {
  const config: Record<
    Exclude<TooltipStatus, "none">,
    { label: string; className: string; dot: string }
  > = {
    profitable: {
      label: "Rentable",
      className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
      dot: "bg-emerald-500",
    },
    below_break_even: {
      label: "Bajo break-even",
      className: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
      dot: "bg-amber-500",
    },
    no_pixel: {
      label: "Sin pixel",
      className: "bg-muted text-muted-foreground",
      dot: "bg-muted-foreground",
    },
  };
  const { label, className, dot } = config[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}

function formatTooltipValue(key: string, value: number, currency: string): string {
  if (key === "spend") return formatMoney(value, currency);
  if (key === "roas") return `${value.toFixed(2)}x`;
  if (key === "conversions") return value.toLocaleString("es-PE");
  return value.toLocaleString("es-PE");
}

// ---------------------------------------------------------------------------
// Narrative subtitle
// ---------------------------------------------------------------------------

interface SubtitleArgs {
  filter: InversionChartFilter;
  offerName?: string;
  resultsLabel: string;
  daysCount: number;
  totalSpend: number;
  totalResults: number;
  avgRoas: number | null;
  currency: string;
}

interface SubtitleOutput {
  text: string;
  warn: boolean;
}

function buildSubtitle({
  filter,
  offerName,
  resultsLabel,
  daysCount,
  totalSpend,
  totalResults,
  avgRoas,
  currency,
}: SubtitleArgs): SubtitleOutput {
  const money = (v: number) => formatMoney(v, currency);
  const daysWord = daysCount === 1 ? "día" : "días";

  if (totalSpend <= 0) {
    return {
      text: `No hay inversión registrada en los últimos ${daysCount} ${daysWord}`,
      warn: false,
    };
  }

  if (filter === "branding") {
    // Branding: no ROAS. Focus on awareness. Never tinted red.
    return {
      text: `En los últimos ${daysCount} ${daysWord} invertiste ${money(totalSpend)} en campañas de branding, construyendo awareness de tu marca`,
      warn: false,
    };
  }

  if (filter === "unassigned") {
    return {
      text: `En los últimos ${daysCount} ${daysWord}, ${money(totalSpend)} se gastaron en campañas sin vincular a ninguna offer — asignalas para ver resultados`,
      warn: false,
    };
  }

  // offer & all — same shape, different subject
  const subject = filter === "offer" && offerName ? offerName : "Meta Ads";

  const warn = avgRoas != null && avgRoas < 1;

  // Prefer ROAS narrative if available, otherwise fall back to result count.
  if (avgRoas != null && totalResults > 0) {
    // Generated = totalSpend * avgRoas (approximate narrative — the exact
    // revenue is not in the timeSeries, so we compute it from the period's
    // average ROAS).
    const generated = totalSpend * avgRoas;
    const base = `En los últimos ${daysCount} ${daysWord} invertiste ${money(totalSpend)} en ${subject} y generaste ${money(generated)} en ventas — ROAS ${avgRoas.toFixed(2)}x`;
    return {
      text: warn ? `${base} — por debajo de break-even` : base,
      warn,
    };
  }

  // Fallback — no ROAS, show result count.
  const plural =
    totalResults === 1 ? resultsLabel.toLowerCase().replace(/s$/, "") : resultsLabel.toLowerCase();
  return {
    text: `En los últimos ${daysCount} ${daysWord} invertiste ${money(totalSpend)} en ${subject} y lograste ${totalResults.toLocaleString("es-PE")} ${plural}`,
    warn: false,
  };
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

export function InversionChart({ timeSeries, filter = "all", offerName }: InversionChartProps) {
  const { currency: tenantCurrency } = useTenantLocale();

  const compositeData = buildCompositeData(timeSeries);

  // Label for the secondary series — "Leads", "Compras", etc. when an offer
  // is selected; otherwise the generic "Resultados".
  const conversionsSeries = timeSeries.find((ts) => ts.metricName === "conversions");
  const resultsLabel = conversionsSeries?.displayName?.trim() || "Resultados";

  // Whether to render the dashed "Resultados" line on the right axis. Hidden
  // for branding (no attribution) and unassigned (no offer attribution).
  const showResultsLine = filter !== "branding" && filter !== "unassigned";
  // Whether to render the ROAS line and reference line. Branding has no ROAS.
  const showRoasLine = filter !== "branding" && filter !== "unassigned";
  // For the tooltip: status chip is only meaningful when ROAS is expected.
  const expectsRoas = showRoasLine;

  // ---------- Empty state ----------
  if (compositeData.length === 0) {
    // Filter-specific empty copy.
    const emptyCopy: Record<InversionChartFilter, string> = {
      all: "No hay inversión registrada en este período",
      offer: offerName
        ? `No hay inversión registrada para ${offerName} en este período`
        : "No hay inversión registrada para esta offer en este período",
      branding: "Sin inversión de branding en este período",
      unassigned: "Sin inversión de campañas sin asignar en este período",
    };
    return (
      <div
        className="rounded-lg border bg-card p-5"
        role="img"
        aria-label={`Gráfico de inversión vs resultados. ${emptyCopy[filter]}.`}
      >
        <ChartInfoTooltip
          title="Inversión y Retorno"
          description="Barras = inversión diaria coloreadas por ROAS (verde = rentable, rojo = bajo break-even). Línea amarilla = ROAS vs meta (break-even en 1.0x)."
        />
        <div className="mt-3 flex flex-col items-center justify-center py-8 text-center">
          <p className="text-sm text-muted-foreground">{emptyCopy[filter]}</p>
        </div>
      </div>
    );
  }

  // ---------- Narrative calculations ----------
  const totalSpend = compositeData.reduce((s, d) => s + d.spend, 0);
  const totalResults = compositeData.reduce((s, d) => s + (d.conversions || 0), 0);
  const daysCount = compositeData.length;
  const roasValues = compositeData.map((d) => d.roas).filter((r): r is number => r != null);
  const avgRoas =
    roasValues.length > 0 ? roasValues.reduce((s, r) => s + r, 0) / roasValues.length : null;

  const { text: subtitleText, warn: subtitleWarn } = buildSubtitle({
    filter,
    offerName,
    resultsLabel,
    daysCount,
    totalSpend,
    totalResults,
    avgRoas,
    currency: tenantCurrency,
  });

  // The chart has data but every "result" is zero on a setup that expects
  // them → show the pixel-off banner above the chart. Branding / unassigned
  // never trigger this because they don't expect attributed results.
  const showPixelOffBanner = expectsRoas && totalResults === 0 && totalSpend > 0;

  // Max spend (for data label on the outlier day — kept from the old chart)
  const maxSpend = Math.max(...compositeData.map((d) => d.spend));

  // A11y summary — read by screen readers only.
  const a11ySummary =
    `Gráfico de inversión vs resultados en los últimos ${daysCount} ${daysCount === 1 ? "día" : "días"}. ` +
    `Total invertido: ${formatMoney(totalSpend, tenantCurrency)}. ` +
    `Total resultados: ${totalResults.toLocaleString("es-PE")}${avgRoas != null ? `. ROAS promedio: ${avgRoas.toFixed(2)} veces` : ""}.`;

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3" role="img" aria-label={a11ySummary}>
      <ChartInfoTooltip
        title="Inversión y Retorno"
        description="Barras = inversión diaria coloreadas por ROAS (verde = rentable, rojo = bajo break-even). Línea amarilla = ROAS vs meta (break-even en 1.0x)."
      />

      <p className={cn("text-xs", subtitleWarn ? "text-red-500" : "text-muted-foreground")}>
        {subtitleText}
      </p>

      {showPixelOffBanner && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-700 dark:text-amber-300"
        >
          <span aria-hidden="true">⚠</span>
          <span>No se registraron resultados — verificá que el Meta Pixel esté configurado</span>
        </div>
      )}

      <ChartContainer
        config={{
          spend: { label: "Inversión", color: COLORS.spend },
          conversions: { label: resultsLabel, color: COLORS.conversions },
          roas: { label: "ROAS", color: COLORS.roas },
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
            tickFormatter={(v: number) => formatMoney(v, tenantCurrency, { compact: true })}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => `${v.toFixed(1)}x`}
          />
          <RechartsTooltip
            content={
              <InversionTooltip
                currency={tenantCurrency}
                resultsLabel={resultsLabel}
                hideStatusChip={!expectsRoas}
                expectsRoas={expectsRoas}
              />
            }
          />
          {showRoasLine && (
            <ReferenceLine
              yAxisId="right"
              y={1}
              stroke="hsl(var(--muted-foreground))"
              strokeDasharray="4 4"
              label={{
                value: "Break-even",
                position: "right",
                fill: "hsl(var(--muted-foreground))",
                fontSize: 10,
              }}
            />
          )}
          <Bar yAxisId="left" dataKey="spend" radius={[3, 3, 0, 0]}>
            {compositeData.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={expectsRoas ? getBarColor(entry.roas) : COLORS.spend} />
            ))}
            <LabelList
              dataKey="spend"
              position="top"
              className="fill-foreground text-[10px] font-medium"
              formatter={(v: number) =>
                v === maxSpend ? formatMoney(v, tenantCurrency, { compact: true }) : ""
              }
            />
          </Bar>
          {showRoasLine && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="roas"
              stroke={COLORS.roas}
              strokeWidth={2}
              dot={false}
            />
          )}
          {showResultsLine && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="conversions"
              stroke={COLORS.conversions}
              strokeWidth={1.5}
              strokeDasharray="6 4"
              dot={false}
            />
          )}
        </ComposedChart>
      </ChartContainer>

      <ul role="list" aria-label="Leyenda del gráfico" className="flex flex-wrap gap-4">
        {expectsRoas ? (
          <>
            <li
              role="listitem"
              className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
            >
              <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: BAR_COLOR_PROFIT }} />
              Rentable (ROAS ≥ 1)
            </li>
            <li
              role="listitem"
              className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
            >
              <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: BAR_COLOR_LOSS }} />
              Bajo break-even
            </li>
          </>
        ) : (
          <li
            role="listitem"
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
          >
            <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: COLORS.spend }} />
            Inversión
          </li>
        )}
        {showRoasLine && (
          <li
            role="listitem"
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
          >
            <span className="h-0.5 w-4 rounded-sm" style={{ backgroundColor: COLORS.roas }} />
            ROAS
          </li>
        )}
        {showResultsLine && (
          <li
            role="listitem"
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
          >
            <span
              className="h-0.5 w-4 rounded-sm border-t border-dashed"
              style={{ borderColor: COLORS.conversions }}
            />
            {resultsLabel}
          </li>
        )}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data transformation
// ---------------------------------------------------------------------------

function buildCompositeData(timeSeries: MetricTimeSeries[]): CompositePoint[] {
  const spendSeries = timeSeries.find((ts) => ts.metricName === "spend");
  const convSeries = timeSeries.find((ts) => ts.metricName === "conversions");
  const roasSeries = timeSeries.find((ts) => ts.metricName === "ROAS");

  if (!spendSeries) return [];

  const raw: CompositePoint[] = spendSeries.dataPoints.map((sp) => {
    const conv = convSeries?.dataPoints.find((c) => c.date === sp.date);
    const roas = roasSeries?.dataPoints.find((r) => r.date === sp.date);
    return {
      isoDate: sp.date,
      date: formatDateEs(sp.date),
      spend: sp.value,
      conversions: conv?.value ?? 0,
      roas: roas?.value ?? null,
    };
  });

  // Filter out zero-activity days
  return raw.filter((d) => d.spend > 0 || d.conversions > 0);
}
