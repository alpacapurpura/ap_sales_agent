"use client";

import { cn } from "@/lib/utils";

import { TONE_CLASSES_IDLE, TONE_CLASSES_SELECTED, TONE_TITLE_CLASSES } from "./entry-shared";

import type { EntrySharedProps } from "./entry-shared";
import type { LaunchEdition } from "../../../types";

interface LanguageEntryProps extends EntrySharedProps {
  variant: LaunchEdition;
}

/**
 * Rail entry for LANGUAGE variant structure (translated editions).
 * Shows: flag + language name + translation status + {completed}/{total}
 * modules + thin progress bar.
 */
export function LanguageEntry({ variant, tone, isSelected, onClick }: LanguageEntryProps) {
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];
  const flag = String(variant.structure_data?.flag_emoji ?? "🌐");
  const progress = variant.structure_data?.translation_progress as number | undefined;
  const total = variant.structure_data?.translation_total as number | undefined;

  const isComplete =
    progress !== undefined && total !== undefined && total > 0 && progress >= total;
  const translationStatus = isComplete ? "Completo" : "En traducción";

  const progressPercent =
    progress !== undefined && total !== undefined && total > 0
      ? Math.round((progress / total) * 100)
      : 0;

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
          {translationStatus}
        </span>
      </div>
      {progress !== undefined && total !== undefined && (
        <p className="mt-1 text-xs text-muted-foreground">
          <strong className="text-foreground">
            {progress}/{total}
          </strong>
          {" módulos traducidos"}
        </p>
      )}
      {/* Thin progress bar — mirrors .entry-capacity in _shared.css */}
      <div
        role="progressbar"
        aria-valuenow={progressPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progreso de traducción: ${progressPercent}%`}
        className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className={cn(
            "h-full rounded-full transition-all",
            isComplete ? "bg-emerald-500" : "bg-amber-400",
          )}
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </button>
  );
}
