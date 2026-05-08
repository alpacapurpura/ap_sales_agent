/**
 * StageMetricsAction — displays stage KPIs with progressive loading tier info.
 *
 * Renders KPI values with currency formatting via useTenantLocale() + formatMoney().
 * Shows truncated alert when row_count exceeds tier threshold.
 * Shows channel breakdown when provided.
 */
"use client";

import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatMoney } from "@/lib/format-money";
import type { ActionComponentProps } from "@/lib/form-runtime/actions/registry";

// ─── Payload types ────────────────────────────────────────────────────────────

interface KpiEntry {
  slug: string;
  value: number;
  currency?: string;
}

interface ChannelBreakdownEntry {
  channel: string;
  value: number;
  currency?: string;
}

interface StageMetricsPayload {
  stage_name: string;
  period: string;
  kpis: KpiEntry[];
  tier_used: 0 | 1 | 2 | 3;
  truncated: boolean;
  row_count?: number;
  channel_breakdown?: ChannelBreakdownEntry[];
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders stage KPI metrics from copilot action payload.
 */
export function StageMetricsAction({ value }: ActionComponentProps<StageMetricsPayload>) {
  const tenantLocale = useTenantLocale();

  return (
    <section
      role="region"
      aria-label={`Métricas de etapa: ${value.stage_name}`}
      className="rounded-lg border p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-base">{value.stage_name}</h3>
        <span className="text-sm text-muted-foreground">{value.period}</span>
      </div>

      {/* Truncated alert */}
      {value.truncated && (
        <div
          role="alert"
          className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800"
        >
          Datos parciales — el volumen supera el umbral del nivel {value.tier_used}.
          {value.row_count !== undefined && (
            <span className="ml-1">({value.row_count.toLocaleString("en-US")} filas)</span>
          )}
        </div>
      )}

      {/* KPI list */}
      <ul className="space-y-1" aria-label="Indicadores clave">
        {value.kpis.map((kpi) => {
          const currency = kpi.currency ?? tenantLocale.currency;
          const formatted = kpi.currency
            ? formatMoney(kpi.value, currency)
            : kpi.value.toLocaleString("en-US");

          return (
            <li key={kpi.slug} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{kpi.slug}</span>
              <span className="font-medium">{formatted}</span>
            </li>
          );
        })}
      </ul>

      {/* Channel breakdown */}
      {value.channel_breakdown && value.channel_breakdown.length > 0 && (
        <div className="pt-2 border-t space-y-1">
          <p className="text-xs text-muted-foreground font-medium">Por canal</p>
          <ul className="space-y-1">
            {value.channel_breakdown.map((entry) => (
              <li key={entry.channel} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{entry.channel}</span>
                <span>
                  {entry.currency
                    ? formatMoney(entry.value, entry.currency ?? tenantLocale.currency)
                    : entry.value.toLocaleString("en-US")}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
