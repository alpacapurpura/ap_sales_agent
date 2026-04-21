"use client";

import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import {
  STATUS_LABELS,
  TONE_CLASSES_IDLE,
  TONE_CLASSES_SELECTED,
  TONE_TITLE_CLASSES,
} from "./entry-shared";

import type { EntrySharedProps } from "./entry-shared";
import type { LaunchEdition } from "../../../types";

interface TierEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
}

/**
 * Extract the price string for a TIER variant.
 * Priority: structure_data.price_amount + price_currency → pricing_override[0] fallback.
 * Never hardcodes a currency — reads from data source per currency-handling rule.
 */
function resolveTierPrice(variant: LaunchEdition): string | null {
  const amount = variant.structure_data?.price_amount as number | undefined;
  const currency = variant.structure_data?.price_currency as string | undefined;
  if (amount !== undefined && currency) {
    return formatMoney(amount, currency);
  }
  const override = variant.pricing_override?.[0];
  if (override) {
    return formatMoney(override.total_amount, override.currency ?? variant.currency);
  }
  return null;
}

/**
 * Rail entry for TIER variant structure (plans: Básico / Premium / Enterprise).
 * Narrower than the full TierVariantCard — focuses on name + price + recommended chip.
 */
export function TierEntry({ variant, tone, isSelected, onClick }: TierEntryProps) {
  const price = resolveTierPrice(variant);
  const isRecommended = variant.structure_data?.is_recommended === true;
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];

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
      {price && (
        <p className="mt-1 text-xs text-muted-foreground">
          <strong className="text-foreground">{price}</strong>
          {" · mensual"}
        </p>
      )}
      {isRecommended && (
        <span className="mt-1.5 inline-block rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
          ★ Recomendado
        </span>
      )}
    </button>
  );
}
