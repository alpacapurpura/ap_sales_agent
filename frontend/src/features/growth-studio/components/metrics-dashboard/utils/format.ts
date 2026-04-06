import { formatMoney } from '@/lib/format-money';

export { formatDualCurrency } from '@/lib/format-money';

export function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

export function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

export function formatCurrency(n: number, currency?: string): string {
  return formatMoney(n, currency || 'USD');
}

export type MetricFormat = 'number' | 'currency' | 'percentage' | 'duration';

export function formatMetricValue(
  value: number,
  format?: MetricFormat,
  currency?: string,
): string {
  switch (format) {
    case 'currency':
      return formatCurrency(value, currency);
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'duration':
      return formatDuration(value);
    default:
      return formatNum(value);
  }
}
