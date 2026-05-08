/**
 * ChannelOverviewAction — displays channel dashboard KPIs from copilot action payload.
 *
 * Renders KPI labels + formatted values. Currency KPIs use formatMoney().
 */
"use client";

import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatMoney } from "@/lib/format-money";
import type { ActionComponentProps } from "@/lib/form-runtime/actions/registry";

// ─── Payload types ────────────────────────────────────────────────────────────

interface DashboardKpi {
  slug: string;
  value: number;
  label: string;
  currency?: string;
}

interface ChannelOverviewPayload {
  channel_name: string;
  period: string;
  dashboard_kpis: DashboardKpi[];
  ui_action?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders channel overview KPIs from copilot action payload.
 */
export function ChannelOverviewAction({ value }: ActionComponentProps<ChannelOverviewPayload>) {
  const tenantLocale = useTenantLocale();

  return (
    <section
      role="region"
      aria-label={`Resumen de canal: ${value.channel_name}`}
      className="rounded-lg border p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-base">{value.channel_name}</h3>
        <span className="text-sm text-muted-foreground">{value.period}</span>
      </div>

      {/* KPI grid */}
      <ul className="grid grid-cols-2 gap-2" aria-label="Indicadores del canal">
        {value.dashboard_kpis.map((kpi) => {
          const currency = kpi.currency ?? tenantLocale.currency;
          const formatted = kpi.currency
            ? formatMoney(kpi.value, currency)
            : kpi.value.toLocaleString("en-US");

          return (
            <li key={kpi.slug} className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">{kpi.label}</span>
              <span className="text-sm font-semibold">{formatted}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
