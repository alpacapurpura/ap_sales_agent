'use client';

import type { ExpansionOfferData } from '../../../types/metrics';

function formatDualCurrency(amount: number, currency: string, usdAmount: number | null): string {
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

interface ExpansionOfferRowProps {
  offer: ExpansionOfferData;
  isChurn?: boolean;
}

export function ExpansionOfferRow({ offer, isChurn = false }: ExpansionOfferRowProps) {
  const revenueText = formatDualCurrency(offer.revenue, offer.currency, offer.usdRevenue);

  return (
    <div className="flex items-center justify-between px-3 py-1.5 text-sm">
      <span className="text-sm">{offer.publicName}</span>
      <div className="flex items-center gap-4 text-sm tabular-nums">
        <div className="flex flex-col items-end">
          <span>{offer.count}</span>
          <span className="text-[10px] text-muted-foreground">transacciones</span>
        </div>
        <span className={isChurn ? 'text-red-600 dark:text-red-400' : ''}>
          {isChurn ? '-' : ''}{revenueText}
        </span>
      </div>
    </div>
  );
}
