"use client";

import { Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { usePersonalityPresets, useSelectPreset } from "../../api/personality";

import type { PresetSummary } from "../../types/personality";

interface PresetCatalogProps {
  onSelected?: () => void;
}

function PresetCard({
  preset,
  isSelected,
  isLoading,
  onSelect,
}: {
  preset: PresetSummary;
  isSelected: boolean;
  isLoading: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={isLoading}
      className={cn(
        "relative w-full text-left rounded-xl border p-4 transition-all duration-200",
        "hover:border-primary/50 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        isSelected ? "border-primary bg-primary/10 ring-1 ring-primary" : "border-border bg-card",
        isLoading && "opacity-60 cursor-not-allowed",
      )}
    >
      {isSelected && (
        <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
          <Check className="w-3 h-3 text-primary-foreground" />
        </div>
      )}

      {/* Icon + Name */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-xl flex-shrink-0">
          {preset.icon}
        </div>
        <div>
          <p className="font-semibold text-sm text-foreground">{preset.name}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{preset.description}</p>

      {/* Sample message */}
      <div className="rounded-lg bg-muted/50 px-3 py-2">
        <p className="text-xs text-foreground/80 italic line-clamp-2">
          &ldquo;{preset.sample_message}&rdquo;
        </p>
      </div>
    </button>
  );
}

export function PresetCatalog({ onSelected }: PresetCatalogProps) {
  const { data: presets, isLoading: loadingPresets, error } = usePersonalityPresets();
  const selectPreset = useSelectPreset();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const handleSelect = async (presetKey: string) => {
    setSelectedKey(presetKey);
    try {
      await selectPreset.mutateAsync(presetKey);
      toast.success("Personalidad configurada correctamente.");
      onSelected?.();
    } catch {
      toast.error("No se pudo seleccionar el preset. Inténtalo de nuevo.");
      setSelectedKey(null);
    }
  };

  if (loadingPresets) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Cargando presets…</span>
      </div>
    );
  }

  if (error || !presets) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        No se pudieron cargar los presets. Recarga la página.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Elige la personalidad base de tu agente. Podrás ajustar las dimensiones después.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {presets.map((preset) => (
          <PresetCard
            key={preset.key}
            preset={preset}
            isSelected={selectedKey === preset.key}
            isLoading={selectPreset.isPending && selectedKey === preset.key}
            onSelect={() => void handleSelect(preset.key)}
          />
        ))}
      </div>
    </div>
  );
}
