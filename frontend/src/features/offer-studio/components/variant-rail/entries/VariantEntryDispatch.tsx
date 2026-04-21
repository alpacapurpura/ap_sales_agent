"use client";

import { cn } from "@/lib/utils";

import { getVariantStructureMeta } from "../../../lib/variant-structure-catalog";

import { TONE_CLASSES_IDLE, TONE_CLASSES_SELECTED, TONE_TITLE_CLASSES } from "./entry-shared";
import { LanguageEntry } from "./LanguageEntry";
import { ModalityEntry } from "./ModalityEntry";
import { RegionalEntry } from "./RegionalEntry";
import { SkuEntry } from "./SkuEntry";
import { TemporalEntry } from "./TemporalEntry";
import { TierEntry } from "./TierEntry";

import type { EntrySharedProps } from "./entry-shared";
import type { LaunchEdition } from "../../../types";

interface VariantEntryDispatchProps extends EntrySharedProps {
  variant: LaunchEdition;
  /** waitlistCount is only relevant for temporal entries. */
  waitlistCount?: number;
}

/**
 * Polymorphic entry dispatcher for the VariantRail.
 *
 * Reads variant.variant_structure → resolves cardTemplate via
 * getVariantStructureMeta → renders the appropriate entry component.
 *
 * Defensive fallback: renders a minimal entry with just the name + an
 * unknown-structure chip when the catalog doesn't recognise the structure.
 * This protects against backend catalog drift without crashing the rail.
 */
export function VariantEntryDispatch({
  variant,
  tone,
  isSelected,
  onClick,
  waitlistCount = 0,
}: VariantEntryDispatchProps) {
  const meta = getVariantStructureMeta(variant.variant_structure);

  // Temporal dispatch
  if (
    variant.variant_structure === "temporal_cohort" ||
    variant.variant_structure === "temporal_single_date" ||
    variant.variant_structure === "recurring_intake"
  ) {
    return (
      <TemporalEntry
        variant={variant}
        tone={tone}
        isSelected={isSelected}
        onClick={onClick}
        waitlistCount={waitlistCount}
      />
    );
  }

  // Non-temporal dispatch by cardTemplate
  switch (meta?.cardTemplate) {
    case "tier":
      return <TierEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />;
    case "sku":
      return <SkuEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />;
    case "regional":
      return (
        <RegionalEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />
      );
    case "modality":
      return (
        <ModalityEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />
      );
    case "language":
      return (
        <LanguageEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />
      );
    default:
      return (
        <FallbackEntry variant={variant} tone={tone} isSelected={isSelected} onClick={onClick} />
      );
  }
}

// ─── Defensive fallback ───────────────────────────────────────────────────────

function FallbackEntry({
  variant,
  tone,
  isSelected,
  onClick,
}: Omit<VariantEntryDispatchProps, "waitlistCount">) {
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      className={cn(
        "block w-full rounded-lg border border-transparent p-2.5 text-left transition-colors",
        toneClass,
      )}
    >
      <span className={cn("text-sm font-semibold", TONE_TITLE_CLASSES[tone])}>
        {variant.edition_name}
      </span>
      <span className="ml-2 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
        {variant.variant_structure}
      </span>
    </button>
  );
}
