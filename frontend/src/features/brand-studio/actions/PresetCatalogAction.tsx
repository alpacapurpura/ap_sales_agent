"use client";

import { Check, Loader2 } from "lucide-react";
import { useCallback } from "react";
import { toast } from "sonner";

import { usePersonalityPresets, useSelectPreset } from "@/features/brand-studio/api/personality";
import { cn } from "@/lib/utils";

import type { PresetSummary } from "@/features/brand-studio/types/personality";
import type { ActionComponentProps } from "@/lib/form-runtime/actions";

interface PresetCardProps {
  preset: PresetSummary;
  isSelected: boolean;
  isPending: boolean;
  onSelect: (key: string) => void;
}

function PresetCard({ preset, isSelected, isPending, onSelect }: PresetCardProps) {
  const handleClick = useCallback(() => onSelect(preset.key), [onSelect, preset.key]);

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      aria-pressed={isSelected}
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

/**
 * PresetCatalog action — grid of personality presets fetched from the
 * backend. Selecting a preset triggers `useSelectPreset` on the backend
 * (owns the cache invalidation of the active personality query) and
 * bubbles the preset key via `onChange` so the form-runtime can update
 * its section state.
 *
 * The `value` prop is the preset key currently selected (schema-driven
 * or persisted); this drives the highlighted card. If no value is given,
 * nothing is highlighted until the user picks.
 */
export function PresetCatalogAction({ value, onChange }: ActionComponentProps<string | null>) {
  const { data: presets, isLoading, error } = usePersonalityPresets();
  const selectPreset = useSelectPreset();

  const handleSelect = useCallback(
    async (presetKey: string) => {
      try {
        await selectPreset.mutateAsync(presetKey);
        toast.success("Personalidad configurada correctamente.");
        onChange(presetKey);
      } catch {
        toast.error("No se pudo seleccionar el preset. Inténtalo de nuevo.");
      }
    },
    [selectPreset, onChange],
  );

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

  if (error || !presets) {
    return (
      <div role="alert" className="py-8 text-center text-sm text-muted-foreground">
        No se pudieron cargar los presets. Recarga la página.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Elegí la personalidad base de tu agente. Podés ajustar las dimensiones después.
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {presets.map((preset) => (
          <PresetCard
            key={preset.key}
            preset={preset}
            isSelected={value === preset.key}
            isPending={selectPreset.isPending && value !== preset.key}
            onSelect={handleSelect}
          />
        ))}
      </div>
    </div>
  );
}
