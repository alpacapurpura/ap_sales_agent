import { formatMoney } from "@/lib/format-money";
import { formatTenantDateTime } from "@/lib/format-date";

export { formatDualCurrency, formatMoneyDual, formatAggregatedMoney } from "@/lib/format-money";

export function formatLastUpdated(isoDate: string, timezone: string): string {
  return formatTenantDateTime(isoDate, timezone);
}

export function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString("es-ES");
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

export function formatCurrency(n: number, currency: string | undefined, fallback = "USD"): string {
  return formatMoney(n, currency ?? fallback);
}

export type MetricFormat = "number" | "currency" | "percentage" | "duration";

export function formatMetricValue(value: number, format?: MetricFormat, currency?: string): string {
  switch (format) {
    case "currency":
      return formatCurrency(value, currency ?? "USD");
    case "percentage":
      return `${value.toFixed(1)}%`;
    case "duration":
      return formatDuration(value);
    default:
      return formatNum(value);
  }
}
