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

interface RegionalEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
}

/**
 * Rail entry for REGIONAL variant structure (geo-segmented pricing).
 * Shows: flag + country name + local price + tax label + locale chip.
 * Currency always comes from structure_data.price_currency — never hardcoded.
 */
export function RegionalEntry({ variant, tone, isSelected, onClick }: RegionalEntryProps) {
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  const flag = String(variant.structure_data?.flag_emoji ?? "🌎");
  const locale = String(variant.structure_data?.locale ?? "");
  const taxLabel = String(variant.structure_data?.tax_label ?? "");
  const priceAmount = variant.structure_data?.price_amount as number | undefined;
  const priceCurrency = variant.structure_data?.price_currency as string | undefined;
  const priceStr =
    priceAmount !== undefined && priceCurrency ? formatMoney(priceAmount, priceCurrency) : null;

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
          {flag} {variant.edition_name}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {STATUS_LABELS[variant.status]}
        </span>
      </div>
      {priceStr && (
        <p className="mt-1 text-xs text-muted-foreground">
          <strong className="text-foreground">{priceStr}</strong>
          {taxLabel ? ` · ${taxLabel}` : ""}
        </p>
      )}
      {locale && (
        <span className="mt-1.5 inline-block rounded bg-sky-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-sky-700">
          {locale}
        </span>
      )}
    </button>
  );
}
