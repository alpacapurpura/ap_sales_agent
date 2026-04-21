"use client";

import { cn } from "@/lib/utils";

import { EditionStatus, EditionVisibility } from "../../../types";

import {
  TONE_CLASSES_IDLE,
  TONE_CLASSES_SELECTED,
  TONE_TITLE_CLASSES,
  STATUS_LABELS,
} from "./entry-shared";

import type { EntrySharedProps } from "./entry-shared";
import type { LaunchEdition } from "../../../types";

interface TemporalEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
  waitlistCount: number;
}

function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return "Sin fecha";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
  });
}

function formatMonthYear(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", { month: "short", year: "2-digit" });
}

/**
 * Entry component for temporal variant structures (temporal_cohort,
 * temporal_single_date, recurring_intake). Extracted from the legacy
 * EditionsRail.tsx EditionEntry inner function — same visual output,
 * now independently testable and composable.
 */
export function TemporalEntry({
  variant,
  tone,
  isSelected,
  waitlistCount,
  onClick,
}: TemporalEntryProps) {
  const isPublic = variant.visibility === EditionVisibility.PUBLIC;
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  const isPast =
    variant.status === EditionStatus.COMPLETED || variant.status === EditionStatus.CANCELLED;

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
          Edición #{variant.edition_number}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {STATUS_LABELS[variant.status]}
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {isPast ? formatMonthYear(variant.start_date) : formatShortDate(variant.start_date)}
      </p>
      {variant.capacity ? (
        <p className="text-xs text-muted-foreground">
          {variant.enrollment_count}/{variant.capacity}
          {isPublic ? " · 🌐 Pública" : " · 🔒 Privada"}
        </p>
      ) : null}
      {waitlistCount > 0 ? (
        <p className="mt-1 text-xs text-purple-700">⚠ {waitlistCount} en waitlist</p>
      ) : null}
    </button>
  );
}
