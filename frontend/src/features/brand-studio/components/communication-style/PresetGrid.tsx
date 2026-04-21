"use client";

import { Check, Loader2 } from "lucide-react";
import { useCallback } from "react";

import { cn } from "@/lib/utils";

import type { PresetSummary } from "@/features/brand-studio/types/personality";

interface PresetCardItemProps {
  preset: PresetSummary;
  isSelected: boolean;
  isPending: boolean;
  onSelect: (key: string) => void;
}

function PresetCardItem({ preset, isSelected, isPending, onSelect }: PresetCardItemProps) {
  const handleClick = useCallback(() => onSelect(preset.key), [onSelect, preset.key]);

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      aria-pressed={isSelected}
      role="button"
      tabIndex={0}
      className={cn(
        "relative w-full rounded-xl border p-4 text-left transition-all duration-200",
        "hover:border-primary/50 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        isSelected ? "border-primary bg-primary/10 ring-1 ring-primary" : "border-border bg-card",
        isPending && "cursor-not-allowed opacity-60",
      )}
    >
      {isSelected && (
        <div className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
          <Check className="h-3 w-3 text-primary-foreground" />
        </div>
      )}
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-muted text-xl">
          {preset.icon}
        </div>
        <p className="text-sm font-semibold text-foreground">{preset.name}</p>
      </div>
      <p className="mb-3 line-clamp-2 text-xs text-muted-foreground">{preset.description}</p>
      <div className="rounded-lg bg-muted/50 px-3 py-2">
        <p className="line-clamp-2 text-xs italic text-foreground/80">
          &ldquo;{preset.sample_message}&rdquo;
        </p>
      </div>
    </button>
  );
}

export interface PresetGridProps {
  presets: PresetSummary[];
  /** Currently selected preset key, or null if none. */
  selectedKey: string | null;
  /** Called when the user clicks a preset card. */
  onSelect: (key: string) => void;
  /** Whether a selection mutation is in flight. Disables all cards. */
  isPending?: boolean;
  isLoading?: boolean;
  error?: Error | null;
}

/**
 * Grid of personality preset cards. Renders a 2-column responsive grid of
 * `PresetCardItem` components. Shows loading/error states inline.
 *
 * Extracted from `PresetCatalogAction` to be reused by both the action
 * wrapper and the new `PresetPickerView` in the Estilo section.
 */
export function PresetGrid({
  presets,
  selectedKey,
  onSelect,
  isPending = false,
  isLoading = false,
  error = null,
}: PresetGridProps) {
  if (isLoading) {
    return (
      <div
        role="status"
        className="flex items-center justify-center gap-2 py-12 text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">Cargando presets…</span>
      </div>
    );
  }

  if (error ?? presets.length === 0) {
    return (
      <div role="alert" className="py-8 text-center text-sm text-muted-foreground">
        No se pudieron cargar los presets. Recarga la página.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {presets.map((preset) => (
        <PresetCardItem
          key={preset.key}
          preset={preset}
          isSelected={selectedKey === preset.key}
          isPending={isPending && selectedKey !== preset.key}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
