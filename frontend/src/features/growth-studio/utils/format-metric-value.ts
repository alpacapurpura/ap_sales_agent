import { formatMoney } from "@/lib/format-money";

/**
 * Unified metric value formatter for Growth Studio.
 * Replaces 6+ scattered `formatValue()` implementations.
 */
export function formatMetricValue(
  value: number,
  unit: string,
  options?: {
    currency?: string;
    percentDecimals?: number;
  },
): string {
  const currency = options?.currency ?? "USD";
  const percentDecimals = options?.percentDecimals ?? 2;

  switch (unit) {
    case "currency":
      if (value === 0) return "--";
      return formatMoney(value, currency);
    case "percentage":
      return `${value.toFixed(percentDecimals)}%`;
    case "ratio":
      return `${value.toFixed(2)}x`;
    default:
      return formatCount(value);
  }
}

function formatCount(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 10_000) return `${(value / 1000).toFixed(0)}k`;
  if (abs >= 1_000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString("en-US");
}
