"use client";

import { Loader2, ShieldCheck, AlertTriangle, AlertCircle, Info } from "lucide-react";
import {
  Pie,
  PieChart,
  Cell,
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ReferenceArea,
} from "recharts";

import { cn } from "@/lib/utils";
import { ChartContainer } from "@/components/ui/chart";
import { MetricInfoPopover } from "@/components/shared/MetricInfoPopover";
import { useMailHealth } from "../../../../../hooks/useMailDashboard";
import { formatMetricValue } from "../../../../../utils/format-metric-value";
import { MailHealthScore } from "../MailHealthScore";
import { ChartSection } from "../../shared/ChartSection";
import { ChartInfoTooltip } from "../../shared/ChartInfoTooltip";
import type { MetaAdsPeriod, MetricKpiData } from "../../../../../types/metrics";
import type { EmailHealthData, BounceBreakdown } from "../../../../../types/mail-types";

interface MailEntregabilidadV2TabProps {
  period: MetaAdsPeriod;
}

// KPI definitions with severity thresholds
const HEALTH_KPIS = [
  {
    metricName: "deliverability_rate",
    description:
      "Porcentaje de emails que llegan al inbox del destinatario. Menos de 95% indica problemas.",
    formula: "Entregados / Enviados x 100",
    thresholds: { warning: 97, critical: 95 },
    lowerIsBetter: false,
  },
  {
    metricName: "bounce_rate",
    description:
      "Porcentaje de emails que rebotan. Los rebotes duros dañan tu reputación permanentemente.",
    formula: "(Hard Bounces + Soft Bounces) / Enviados x 100",
    thresholds: { warning: 2, critical: 5 },
    lowerIsBetter: true,
  },
  {
    metricName: "unsubscribe_rate",
    description:
      "Porcentaje de destinatarios que se dan de baja. Alta tasa indica contenido irrelevante.",
    formula: "Bajas / Entregados x 100",
    thresholds: { warning: 0.2, critical: 0.5 },
    lowerIsBetter: true,
  },
  {
    metricName: "forward_rate",
    description: "Porcentaje de emails reenviados. Indica contenido tan valioso que lo comparten.",
    formula: "Reenvíos / Entregados x 100",
    thresholds: { warning: 0.5, critical: 0.1 },
    lowerIsBetter: false,
  },
];

function getSeverityColor(
  value: number,
  thresholds: { warning: number; critical: number },
  lowerIsBetter: boolean,
): string {
  if (lowerIsBetter) {
    if (value >= thresholds.critical) return "text-red-600";
    if (value >= thresholds.warning) return "text-amber-600";
    return "text-emerald-600";
  }
  if (value <= thresholds.critical) return "text-red-600";
  if (value <= thresholds.warning) return "text-amber-600";
  return "text-emerald-600";
}

function getSeverityBorder(
  value: number,
  thresholds: { warning: number; critical: number },
  lowerIsBetter: boolean,
): string {
  if (lowerIsBetter) {
    if (value >= thresholds.critical) return "border-t-red-500";
    if (value >= thresholds.warning) return "border-t-amber-500";
    return "border-t-emerald-500";
  }
  if (value <= thresholds.critical) return "border-t-red-500";
  if (value <= thresholds.warning) return "border-t-amber-500";
  return "border-t-emerald-500";
}

// Donut chart colors
const DONUT_COLORS = ["hsl(0, 84%, 60%)", "hsl(38, 92%, 50%)", "hsl(142, 71%, 45%)"];

export function MailEntregabilidadV2Tab({ period }: MailEntregabilidadV2TabProps) {
  const { data, isLoading } = useMailHealth(period);

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
          <ShieldCheck className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin datos de entregabilidad</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Los datos de salud se generarán cuando tengas historial de envíos de email.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto">
      {/* Section 1: Emails Sent + Health Score */}
      <ChartSection slug="salud-email">
        <EmailsSentWithHealth data={data} />
      </ChartSection>

      {/* Section 2: KPI Cards */}
      <ChartSection slug="kpis-entregabilidad">
        <HealthKpiCards data={data} />
      </ChartSection>

      {/* Section 3: Bounce Breakdown + Deliverability Trend */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartSection slug="desglose-rebotes">
          <BounceDonut breakdown={data.bounceBreakdown} />
        </ChartSection>

        <ChartSection slug="tendencia-entregabilidad">
          <DeliverabilityTrend data={data} />
        </ChartSection>
      </div>

      {/* Section 4: Alerts */}
      {data.alerts.length > 0 && (
        <ChartSection slug="alertas-entregabilidad">
          <AlertsList alerts={data.alerts} />
        </ChartSection>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function EmailsSentWithHealth({ data }: { data: EmailHealthData }) {
  return (
    <div className="flex gap-4 items-stretch">
      {/* Campaigns Count */}
      <div className="rounded-lg border bg-card p-4 flex flex-col items-center justify-center min-w-[120px]">
        <span className="text-[11px] text-muted-foreground uppercase tracking-wider text-center">
          Envíos
        </span>
        <span className="text-3xl font-bold tabular-nums mt-1">{data.campaignsCount}</span>
        <span className="text-[10px] text-muted-foreground mt-0.5">campañas enviadas</span>
      </div>

      {/* Health Score */}
      <div className="flex-1">
        <MailHealthScore healthScore={data.healthScore} />
      </div>
    </div>
  );
}

function HealthKpiCards({ data }: { data: EmailHealthData }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {HEALTH_KPIS.map((config) => {
        const kpi = data.kpis.find((k) => k.metricName === config.metricName);
        if (!kpi) return null;

        const value = kpi.currentValue;
        const colorClass = getSeverityColor(value, config.thresholds, config.lowerIsBetter);
        const borderClass = getSeverityBorder(value, config.thresholds, config.lowerIsBetter);

        const formattedValue = formatMetricValue(value, kpi.unit, {
          currency: kpi.currency,
          percentDecimals: 2,
        });

        return (
          <div
            key={kpi.metricName}
            className={cn("rounded-lg border border-t-[3px] bg-card p-3.5 space-y-1", borderClass)}
          >
            <MetricInfoPopover
              displayName={kpi.displayName}
              description={config.description}
              formula={config.formula}
              benchmark={kpi.benchmark ? { value: kpi.benchmark.median } : undefined}
            >
              <span className="text-[11px] text-muted-foreground">{kpi.displayName}</span>
            </MetricInfoPopover>

            <p className={cn("text-xl font-semibold tabular-nums", colorClass)}>{formattedValue}</p>

            {kpi.deltaPct != null && <DeltaIndicator kpi={kpi} />}
          </div>
        );
      })}
    </div>
  );
}

function DeltaIndicator({ kpi }: { kpi: MetricKpiData }) {
  if (kpi.deltaPct == null) return null;

  const isPositive = kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0;

  return (
    <div className="flex items-center gap-1">
      <span
        className={cn(
          "inline-flex items-center gap-0.5 text-[11px] font-medium",
          isPositive ? "text-emerald-600" : "text-red-600",
        )}
      >
        {kpi.unit === "percentage"
          ? `${kpi.deltaAbsolute != null ? Math.abs(kpi.deltaAbsolute).toFixed(2) : "0"}pp`
          : `${Math.abs(kpi.deltaPct).toFixed(0)}%`}
        <span className="text-muted-foreground font-normal"> vs anterior</span>
      </span>
    </div>
  );
}

function BounceDonut({ breakdown }: { breakdown: BounceBreakdown }) {
  const donutData = [
    { name: "Rebotes duros", value: breakdown.hardBounces },
    { name: "Rebotes suaves", value: breakdown.softBounces },
    { name: "Entregados", value: breakdown.totalDelivered },
  ];

  const total = breakdown.hardBounces + breakdown.softBounces + breakdown.totalDelivered;

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Desglose de Rebotes"
        description="Rebotes duros = direcciones inválidas (permanentes). Suaves = buzón lleno o temporales. Los duros dañan tu reputación."
      />

      <div className="flex items-center gap-6">
        <ChartContainer
          config={{
            hard: { label: "Duros", color: DONUT_COLORS[0] },
            soft: { label: "Suaves", color: DONUT_COLORS[1] },
            delivered: { label: "Entregados", color: DONUT_COLORS[2] },
          }}
          className="h-[160px] w-[160px] shrink-0"
        >
          <PieChart>
            <Pie
              data={donutData}
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
            >
              {donutData.map((_, i) => (
                <Cell key={i} fill={DONUT_COLORS[i]} />
              ))}
            </Pie>
            <RechartsTooltip />
          </PieChart>
        </ChartContainer>

        <div className="space-y-2 flex-1">
          <LegendItem
            color="bg-red-500"
            label="Rebotes duros"
            value={breakdown.hardBounces.toLocaleString("en-US")}
            pct={total > 0 ? `${breakdown.hardBounceRate.toFixed(2)}%` : "0%"}
          />
          <LegendItem
            color="bg-amber-500"
            label="Rebotes suaves"
            value={breakdown.softBounces.toLocaleString("en-US")}
            pct={total > 0 ? `${breakdown.softBounceRate.toFixed(2)}%` : "0%"}
          />
          <LegendItem
            color="bg-emerald-500"
            label="Entregados"
            value={breakdown.totalDelivered.toLocaleString("en-US")}
            pct={total > 0 ? `${((breakdown.totalDelivered / total) * 100).toFixed(1)}%` : "0%"}
          />
        </div>
      </div>
    </div>
  );
}

function LegendItem({
  color,
  label,
  value,
  pct,
}: {
  color: string;
  label: string;
  value: string;
  pct: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className={cn("h-2.5 w-2.5 rounded-full shrink-0", color)} />
      <div className="flex items-center justify-between flex-1 text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold tabular-nums">
          {value} <span className="text-muted-foreground font-normal">({pct})</span>
        </span>
      </div>
    </div>
  );
}

function DeliverabilityTrend({ data }: { data: EmailHealthData }) {
  const bounceRateSeries = data.timeSeries.find((ts) => ts.metricName === "bounce_rate");
  const unsubRateSeries = data.timeSeries.find((ts) => ts.metricName === "unsubscribe_rate");

  const trendMap = new Map<string, Record<string, string | number>>();
  for (const ts of [bounceRateSeries, unsubRateSeries].filter(Boolean)) {
    for (const dp of ts!.dataPoints) {
      const entry = trendMap.get(dp.date) ?? ({ date: dp.date } as Record<string, string | number>);
      entry[ts!.metricName] = dp.value;
      trendMap.set(dp.date, entry);
    }
  }

  const trendData = Array.from(trendMap.values())
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map((d) => ({ ...d, date: String(d.date).slice(5) }));

  if (trendData.length < 2) {
    return (
      <div className="rounded-lg border bg-card p-5">
        <ChartInfoTooltip
          title="Tendencia de Entregabilidad"
          description="Necesitas al menos 2 periodos de datos para ver la tendencia."
        />
        <p className="text-sm text-muted-foreground mt-2">
          Datos insuficientes para mostrar tendencia.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Tendencia de Entregabilidad"
        description="Evolución de bounce rate y desuscripción. La zona roja indica niveles peligrosos."
      />
      <ChartContainer
        config={{
          bounce_rate: { label: "Bounce Rate", color: "hsl(0, 84%, 60%)" },
          unsubscribe_rate: { label: "Desuscripción", color: "hsl(38, 92%, 50%)" },
        }}
        className="h-[200px] w-full"
      >
        <LineChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="date" className="text-xs" />
          <YAxis className="text-xs" unit="%" />
          <RechartsTooltip />
          {/* Danger zone shading */}
          <ReferenceArea y1={5} y2={100} fill="hsl(0, 84%, 60%)" fillOpacity={0.05} />
          <Line
            type="monotone"
            dataKey="bounce_rate"
            stroke="var(--color-bounce_rate)"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="unsubscribe_rate"
            stroke="var(--color-unsubscribe_rate)"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ChartContainer>
      <div className="flex gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-red-500" />
          Bounce Rate
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          Desuscripción
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="h-2 w-3 bg-red-500/10" />
          Zona peligrosa
        </div>
      </div>
    </div>
  );
}

function AlertsList({ alerts }: { alerts: string[] }) {
  function getAlertIcon(index: number) {
    if (index === 0) return <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />;
    if (index < 3) return <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />;
    return <Info className="h-4 w-4 text-blue-500 shrink-0" />;
  }

  function getAlertBorder(index: number) {
    if (index === 0) return "border-l-red-500";
    if (index < 3) return "border-l-amber-500";
    return "border-l-blue-500";
  }

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Alertas de Entregabilidad"
        description="Problemas detectados que pueden afectar la capacidad de entrega de tus emails."
      />
      <div className="space-y-2">
        {alerts.map((alert, idx) => (
          <div
            key={idx}
            className={cn(
              "flex items-start gap-2.5 rounded-md border-l-[3px] bg-muted/20 px-3 py-2.5",
              getAlertBorder(idx),
            )}
          >
            {getAlertIcon(idx)}
            <p className="text-xs text-muted-foreground leading-relaxed">{alert}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
