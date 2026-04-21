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

interface ModalityEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
}

const MODE_ICONS: Record<string, string> = {
  presencial: "🏢",
  online: "💻",
  hibrido: "🔀",
  híbrido: "🔀",
};

function getModeIcon(mode: string): string {
  return MODE_ICONS[mode.toLowerCase()] ?? "📍";
}

/**
 * Rail entry for MODALITY variant structure (presencial / online / híbrido).
 * Shows: mode icon + name + price + logistics summary (cupos for presencial,
 * platform for online).
 * Currency comes from structure_data.price_currency — never hardcoded.
 */
export function ModalityEntry({ variant, tone, isSelected, onClick }: ModalityEntryProps) {
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  const mode = String(variant.structure_data?.mode ?? "");
  const modeIcon = getModeIcon(mode);
  const priceAmount = variant.structure_data?.price_amount as number | undefined;
  const priceCurrency = variant.structure_data?.price_currency as string | undefined;
  const priceStr =
    priceAmount !== undefined && priceCurrency ? formatMoney(priceAmount, priceCurrency) : null;

  const venue = variant.structure_data?.venue as string | undefined;
  const { capacity } = variant;
  const enrollmentCount = variant.enrollment_count;

  // Logistics summary: "CDMX · 12/20 cupos" for presencial, "Zoom · ilimitado" for online
  let logisticsSummary: string | null = null;
  if (mode === "presencial" && capacity !== null && capacity !== undefined) {
    const location = venue ?? "";
    logisticsSummary = location
      ? `${location} · ${enrollmentCount}/${capacity} cupos`
      : `${enrollmentCount}/${capacity} cupos`;
  } else if (mode === "online") {
    const platform = (variant.structure_data?.platform as string | undefined) ?? "Zoom";
    const maxStr = capacity === null || capacity === undefined ? "ilimitado" : String(capacity);
    logisticsSummary = `${platform} · ${maxStr}`;
  } else if ((mode === "hibrido" || mode === "híbrido") && variant.structure_data?.schedule) {
    logisticsSummary = String(variant.structure_data.schedule);
  }

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
          {modeIcon} {variant.edition_name}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {STATUS_LABELS[variant.status]}
        </span>
      </div>
      {priceStr && (
        <p className="mt-1 text-xs text-muted-foreground">
          <strong className="text-foreground">{priceStr}</strong>
          {" · mensual"}
        </p>
      )}
      {logisticsSummary && (
        <p className="mt-0.5 text-xs text-muted-foreground">{logisticsSummary}</p>
      )}
    </button>
  );
}
