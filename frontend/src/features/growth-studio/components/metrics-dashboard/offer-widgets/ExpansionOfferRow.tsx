"use client";

import { formatDualCurrency } from "@/lib/format-money";

import type { ExpansionOfferData } from "../../../types/metrics";

interface ExpansionOfferRowProps {
  offer: ExpansionOfferData;
  isChurn?: boolean;
}

/**
 *
 */
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
        <span className={isChurn ? "text-red-600 dark:text-red-400" : ""}>
          {isChurn ? "-" : ""}
          {revenueText}
        </span>
      </div>
    </div>
  );
}
