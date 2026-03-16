'use client';

interface RevenueGroupHeaderProps {
  groupLabel: string;
  subtitle: string;
  totalRevenue: number;
  totalRevenueUsd: number | null;
  currency: string;
  customerCount: number;
  revenuePercentage: number;
}

function formatRevenue(amount: number, currency: string, usdAmount: number | null): string {
  const fmt = new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  const main = fmt.format(amount);

  if (currency === 'USD') return main;
  if (usdAmount != null) {
    const usdFmt = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${main} (~${usdFmt.format(usdAmount)} USD)`;
  }
  return main;
}

export function RevenueGroupHeader({
  groupLabel,
  subtitle,
  totalRevenue,
  totalRevenueUsd,
  currency,
  customerCount,
  revenuePercentage,
}: RevenueGroupHeaderProps) {
  return (
    <div className="px-3 py-2">
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-sm font-semibold">{groupLabel}</span>
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 tabular-nums">
            {formatRevenue(totalRevenue, currency, totalRevenueUsd)}
          </span>
          <span className="text-xs text-muted-foreground">
            {customerCount} clientes | {revenuePercentage.toFixed(1)}% del total
          </span>
        </div>
      </div>
    </div>
  );
}
