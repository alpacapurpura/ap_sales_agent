"use client";

import { RefreshCw } from "lucide-react";

import type { OfferSaleData } from "../../../types/metrics";

interface OfferMetricsRowProps {
  offer: OfferSaleData;
  tierKey: string;
  /** Callback when user clicks the revenue value to open drill-down sidebar */
  onRevenueClick?: () => void;
}

function getTierIndicator(tierKey: string) {
  switch (tierKey) {
    case "low_ticket":
      return <span className="text-xs font-medium text-muted-foreground">$</span>;
    case "mid_ticket":
      return <span className="text-xs font-medium text-muted-foreground">$$</span>;
    case "high_ticket":
      return <span className="text-xs font-medium text-muted-foreground">$$$</span>;
    case "recurrente":
      return <RefreshCw className="h-4 w-4 text-muted-foreground" />;
    default:
      return null;
  }
}

function formatRevenue(amount: number, currency: string, usdAmount: number | null): string {
  const fmt = new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  const main = fmt.format(amount);

  if (currency === "USD") {
    return main;
  }

  if (usdAmount != null) {
    const usdFmt = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${main} (~${usdFmt.format(usdAmount)} USD)`;
  }

  return main;
}

export function OfferMetricsRow({ offer, tierKey, onRevenueClick }: OfferMetricsRowProps) {
  const {
    publicName,
    salesCount,
    totalRevenue,
    currency,
    usdRevenue,
    sourceBreakdown,
    newSubscriptions,
    newSubscriptionRevenue,
    renewals,
    renewalRevenue,
    subscriptionNewLabel,
    subscriptionRenewalLabel,
  } = offer;

  const sources = Object.entries(sourceBreakdown)
    .filter(([, count]) => count > 0)
    .map(([source, count]) => `${source}: ${count}`)
    .join(" | ");

  const hasSubscriptionData = newSubscriptions != null || renewals != null;

  const subFmt = (amount: number | null) =>
    amount != null
      ? new Intl.NumberFormat("es-MX", {
          style: "currency",
          currency,
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(amount)
      : "";

  return (
    <div className="rounded-lg border p-3 hover:bg-muted/50 transition-colors">
      {/* Line 1: Tier indicator + Name + Sales count | Revenue */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getTierIndicator(tierKey)}
          <span className="text-sm font-medium">{publicName}</span>
          <span className="text-xs text-muted-foreground ml-2">{salesCount} ventas</span>
        </div>
        {onRevenueClick ? (
          <button
            onClick={onRevenueClick}
            className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 tabular-nums cursor-pointer hover:opacity-80 hover:underline transition-opacity duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20 rounded px-1"
            title="Ver detalle de revenue"
          >
            {formatRevenue(totalRevenue, currency, usdRevenue)}
          </button>
        ) : (
          <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 tabular-nums">
            {formatRevenue(totalRevenue, currency, usdRevenue)}
          </span>
        )}
      </div>

      {/* Line 2: Source breakdown */}
      {sources && <p className="text-xs text-muted-foreground mt-1">{sources}</p>}

      {/* Line 3: Subscription split (conditional) */}
      {hasSubscriptionData && (
        <p className="text-xs text-muted-foreground mt-1">
          {newSubscriptions != null && subscriptionNewLabel && (
            <>
              {newSubscriptions} {subscriptionNewLabel} ({subFmt(newSubscriptionRevenue)})
            </>
          )}
          {newSubscriptions != null && renewals != null && " | "}
          {renewals != null && subscriptionRenewalLabel && (
            <>
              {renewals} {subscriptionRenewalLabel} ({subFmt(renewalRevenue)})
            </>
          )}
        </p>
      )}
    </div>
  );
}
