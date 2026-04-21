"use client";

import { cn } from "@/lib/utils";

import {
  STATUS_LABELS,
  TONE_CLASSES_IDLE,
  TONE_CLASSES_SELECTED,
  TONE_TITLE_CLASSES,
} from "./entry-shared";

import type { EntrySharedProps } from "./entry-shared";
import type { LaunchEdition } from "../../../types";

interface SkuEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
}

function getLowStockThreshold(variant: LaunchEdition): number {
  const threshold = variant.structure_data?.low_stock_threshold;
  return typeof threshold === "number" ? threshold : 10;
}

/**
 * Rail entry for SKU_VARIANT structure (physical products with inventory tracking).
 * Shows: variant name + SKU code + unit count + low-stock warning when applicable.
 */
export function SkuEntry({ variant, tone, isSelected, onClick }: SkuEntryProps) {
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  const skuCode = String(variant.structure_data?.sku_code ?? "—");
  const threshold = getLowStockThreshold(variant);
  const { capacity } = variant;
  const isLowStock =
    capacity !== null && capacity !== undefined && capacity > 0 && capacity <= threshold;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      aria-current={isSelected ? "true" : undefined}
      className={cn(
        "block w-full rounded-lg border border-transparent p-2.5 text-left transition-colors",
        toneClass,
      )}
    >
      <div className="flex items-center justify-between">
        <span className={cn("text-sm font-semibold", TONE_TITLE_CLASSES[tone])}>
          {variant.edition_name}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {STATUS_LABELS[variant.status]}
        </span>
      </div>
      <p className="mt-1 font-mono text-xs text-muted-foreground">{skuCode}</p>
      {capacity !== null && capacity !== undefined && (
        <p className="mt-0.5 text-xs text-muted-foreground">
          <strong className="text-foreground">{capacity}</strong>
          {" unidades"}
          {isLowStock && <span className="ml-1.5 font-semibold text-orange-600">⚠ Low stock</span>}
        </p>
      )}
    </button>
  );
}
