"use client";

import { formatDualCurrency } from "@/lib/format-money";

import { ExpansionOfferRow } from "./ExpansionOfferRow";

import type { ExpansionGroupData } from "../../../types/metrics";

interface ExpansionGroupProps {
  group: ExpansionGroupData;
  variant?: "default" | "churn";
}

export function ExpansionGroup({ group, variant = "default" }: ExpansionGroupProps) {
  const isChurn = variant === "churn";
  const borderClass = isChurn ? "border-l-2 border-red-200 dark:border-red-800 pl-2" : "";

  return (
    <div className={borderClass}>
      {/* Header section */}
      <div className="px-3 py-2 bg-muted/30 rounded-lg">
        {/* Title row */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">{group.groupLabel}</span>
          {group.ratePct != null && (
            <span
              className={`text-sm font-semibold tabular-nums ${isChurn ? "text-red-600 dark:text-red-400" : ""}`}
            >
              {group.ratePct.toFixed(1)}%
            </span>
          )}
        </div>
        {/* Subtitle */}
        <p className="text-xs text-muted-foreground">{group.groupSubtitle}</p>
        {/* Aggregate row */}
        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
          <span>{group.totalCount} transacciones</span>
          <span className={isChurn ? "text-red-600 dark:text-red-400" : ""}>
            {isChurn ? "-" : ""}
            {formatDualCurrency(group.totalRevenue, group.currency, group.totalRevenueUsd)}
          </span>
        </div>
      </div>

      {/* Offer rows */}
      {group.offers.length > 0 ? (
        <div className="space-y-0">
          {group.offers.map((o) => (
            <ExpansionOfferRow key={o.offerId} offer={o} isChurn={isChurn} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground px-3 py-2">Sin transacciones en este periodo</p>
      )}
    </div>
  );
}
