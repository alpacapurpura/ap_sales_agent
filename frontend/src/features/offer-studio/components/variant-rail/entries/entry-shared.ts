/**
 * Shared constants and helpers for VariantRail entry components.
 *
 * Centralised here so that TemporalEntry, TierEntry, SkuEntry, etc. all
 * produce identical tone classes and status labels — avoiding drift between
 * the 6 entry templates.
 */

import { EditionStatus } from "../../../types";

import type { GroupTone } from "../grouping";

export const TONE_CLASSES_SELECTED: Record<GroupTone, string> = {
  active: "bg-emerald-50 border-emerald-200 ring-1 ring-emerald-200/50",
  next: "bg-blue-50 border-blue-200 ring-1 ring-blue-200/50",
  draft: "border-amber-400 bg-amber-50",
  past: "bg-muted border-border",
};

export const TONE_CLASSES_IDLE: Record<GroupTone, string> = {
  active: "hover:bg-emerald-50/60",
  next: "hover:bg-blue-50/60",
  draft: "border-dashed border-amber-300 hover:bg-amber-50",
  past: "hover:bg-muted/50",
};

export const TONE_TITLE_CLASSES: Record<GroupTone, string> = {
  active: "text-emerald-900",
  next: "text-blue-900",
  draft: "text-amber-800",
  past: "text-muted-foreground",
};

export const STATUS_LABELS: Record<EditionStatus, string> = {
  [EditionStatus.DRAFT]: "Borrador",
  [EditionStatus.UPCOMING]: "Próxima",
  [EditionStatus.ACTIVE]: "En curso",
  [EditionStatus.COMPLETED]: "Completa",
  [EditionStatus.CANCELLED]: "Cancelada",
};

/** Shared props that every entry component receives. */
export interface EntrySharedProps {
  tone: GroupTone;
  isSelected: boolean;
  onClick: () => void;
}
