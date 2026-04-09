'use client';

import { Loader2, Bot, TrendingUp, TrendingDown } from 'lucide-react';

import { cn } from '@/lib/utils';
import { MetricInfoPopover } from '@/components/shared/MetricInfoPopover';
import { useMailAutomations } from '../../../../../hooks/useMailDashboard';
import { formatMetricValue } from '../../../../../utils/format-metric-value';
import { ChartSection } from '../../shared/ChartSection';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import type { MetaAdsPeriod, MetricKpiData } from '../../../../../types/metrics';
import type {
  EmailAutomation,
  EmailAutomationsData,
} from '../../../../../types/mail-types';

interface MailAutomatizacionesTabProps {
  period: MetaAdsPeriod;
}

// KPI definitions
const AUTOMATION_KPIS = [
  {
    metricName: 'automation_emails_sent',
    description: 'Total de emails enviados a través de automatizaciones en el periodo.',
  },
  {
    metricName: 'automation_completion_rate',
    description:
      'Porcentaje de suscriptores que completaron la secuencia completa de automatización.',
    formula: 'Completados / Ingresados x 100',
  },
  {
    metricName: 'automation_avg_open_rate',
    description:
      'Tasa de apertura promedio de los emails de automatización. Usualmente mayor que campañas.',
    formula: 'Promedio ponderado de Open Rate de todas las automatizaciones',
  },
];

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  active: { bg: 'bg-emerald-500/10', text: 'text-emerald-500' },
  paused: { bg: 'bg-zinc-500/10', text: 'text-zinc-400' },
};

const TYPE_LABELS: Record<string, string> = {
  welcome: 'Bienvenida',
  nurture: 'Nutrición',
  reengagement: 'Re-engagement',
  post_compra: 'Post-compra',
};

export function MailAutomatizacionesTab({ period }: MailAutomatizacionesTabProps) {
  const { data, isLoading } = useMailAutomations(period);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.automations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
          <Bot className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin automatizaciones</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Las automatizaciones se activarán cuando configures secuencias de email en tu proveedor.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto">
      {/* Section 1: KPI Cards */}
      <ChartSection slug="kpis-automatizaciones">
        <KpiRow data={data} />
      </ChartSection>

      {/* Section 2: Automations Table */}
      <ChartSection slug="tabla-automatizaciones">
        <AutomationsTable automations={data.automations} />
      </ChartSection>

      {/* Section 3: Campaigns vs Automations comparison */}
      <ChartSection slug="comparacion-campanas-auto">
        <CampaignsVsAutoComparison data={data} />
      </ChartSection>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiRow({ data }: { data: EmailAutomationsData }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {AUTOMATION_KPIS.map(config => {
        const kpi = data.kpis.find(k => k.metricName === config.metricName);
        if (!kpi) return null;

        return (
          <KpiCard key={kpi.metricName} kpi={kpi} description={config.description} formula={config.formula} />
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

function AutomationsTable({ automations }: { automations: EmailAutomation[] }) {
  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Automatizaciones Activas"
        description="Listado de secuencias automatizadas con métricas de rendimiento individual."
      />
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead className="text-muted-foreground border-b">
            <tr>
              <th className="py-2 px-2 text-left font-medium">Nombre</th>
              <th className="py-2 px-2 text-center font-medium">Tipo</th>
              <th className="py-2 px-2 text-center font-medium">Estado</th>
              <th className="py-2 px-2 text-center font-medium">Suscriptores</th>
              <th className="py-2 px-2 text-center font-medium">Completados</th>
              <th className="py-2 px-2 text-center font-medium">Open Rate</th>
              <th className="py-2 px-2 text-center font-medium">Click Rate</th>
              <th className="py-2 px-2 text-center font-medium">Completación</th>
            </tr>
          </thead>
          <tbody>
            {automations.map(auto => {
              const statusStyle = STATUS_STYLES[auto.status] ?? STATUS_STYLES.paused;
              const typeLabel = TYPE_LABELS[auto.automationType] ?? auto.automationType;

              return (
                <tr
                  key={auto.automationId}
                  className="border-b border-border/20 hover:bg-muted/20 transition-colors"
                >
                  <td className="py-2.5 px-2 font-medium text-xs max-w-[200px] truncate">
                    {auto.name}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span className="inline-block rounded-full bg-muted/50 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                      {typeLabel}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span
                      className={cn(
                        'inline-block rounded-full px-2 py-0.5 text-[10px] font-medium',
                        statusStyle.bg,
                        statusStyle.text,
                      )}
                    >
                      {auto.status === 'active' ? 'Activa' : 'Pausada'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center tabular-nums">
                    {auto.activeSubscribers.toLocaleString('en-US')}
                  </td>
                  <td className="py-2.5 px-2 text-center tabular-nums">
                    {auto.completed.toLocaleString('en-US')}
                  </td>
                  <td
                    className={cn(
                      'py-2.5 px-2 text-center font-semibold tabular-nums',
                      auto.openRate > 21.5 ? 'text-emerald-600' : 'text-foreground',
                    )}
                  >
                    {auto.openRate.toFixed(1)}%
                  </td>
                  <td
                    className={cn(
                      'py-2.5 px-2 text-center tabular-nums',
                      auto.clickRate > 2.3 && 'text-emerald-600',
                    )}
                  >
                    {auto.clickRate.toFixed(1)}%
                  </td>
                  <td
                    className={cn(
                      'py-2.5 px-2 text-center font-semibold tabular-nums',
                      auto.completionRate > 50
                        ? 'text-emerald-600'
                        : auto.completionRate < 20
                          ? 'text-red-500'
                          : 'text-amber-600',
                    )}
                  >
                    {auto.completionRate.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CampaignsVsAutoComparison({ data }: { data: EmailAutomationsData }) {
  // Compute aggregate automation metrics
  const activeAutomations = data.automations.filter(a => a.status === 'active');
  if (activeAutomations.length === 0) return null;

  const totalSent = activeAutomations.reduce((sum, a) => sum + a.emailsSent, 0);
  const avgOpenRate =
    totalSent > 0
      ? activeAutomations.reduce((sum, a) => sum + a.openRate * a.emailsSent, 0) / totalSent
      : 0;
  const avgClickRate =
    totalSent > 0
      ? activeAutomations.reduce((sum, a) => sum + a.clickRate * a.emailsSent, 0) / totalSent
      : 0;

  // We only show this section if we have meaningful data
  if (totalSent === 0) return null;

  const rows = [
    {
      label: 'Open Rate',
      automations: `${avgOpenRate.toFixed(1)}%`,
    },
    {
      label: 'Click Rate',
      automations: `${avgClickRate.toFixed(1)}%`,
    },
    {
      label: 'Emails Enviados',
      automations: totalSent.toLocaleString('en-US'),
    },
    {
      label: 'Automatizaciones Activas',
      automations: activeAutomations.length.toString(),
    },
  ];

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Resumen de Automatizaciones"
        description="Métricas agregadas de todas las automatizaciones activas."
      />
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[11px] text-muted-foreground border-b">
            <th className="text-left py-2 font-medium">Métrica</th>
            <th className="text-center py-2 font-medium">Valor</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.label} className="border-b border-border/30">
              <td className="py-2.5 text-xs text-muted-foreground">{row.label}</td>
              <td className="py-2.5 text-center font-semibold text-xs">
                {row.automations}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Insight */}
      {avgOpenRate > 21.5 && (
        <div className="rounded-md border-l-[3px] border-emerald-500 bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-emerald-600">Insight:</span>{' '}
            Las automatizaciones tienen +{(avgOpenRate - 21.5).toFixed(0)}% más engagement
            que el promedio de la industria para campañas manuales.
          </p>
        </div>
      )}
    </div>
  );
}
