"use client";

import { Loader2, Save } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useUpdateDimensions } from "@/features/brand-studio/api/personality";
import {
  DIMENSION_LABELS,
  DIMENSION_LEVEL_NAMES,
  getDimensionLevelName,
  type PersonalityDimensions,
} from "@/features/brand-studio/types/personality";
import { cn } from "@/lib/utils";

const DIMENSION_ORDER: (keyof PersonalityDimensions)[] = [
  "energy",
  "warmth",
  "humor",
  "expressiveness",
  "narrative",
  "verbosity",
];

const STEP_COUNT = 5;
const DIMENSION_MIN = 0;
const DIMENSION_MAX = 1;
const DIMENSION_STEP = 0.25;

export const DEFAULT_DIMENSIONS: PersonalityDimensions = {
  energy: 0.5,
  warmth: 0.5,
  humor: 0.5,
  expressiveness: 0.5,
  narrative: 0.5,
  verbosity: 0.5,
};

interface DimensionSliderRowProps {
  dimension: keyof PersonalityDimensions;
  value: number;
  onChange: (val: number) => void;
  disabled?: boolean;
}

function DimensionSliderRow({ dimension, value, onChange, disabled }: DimensionSliderRowProps) {
  const { label, low, high } = DIMENSION_LABELS[dimension];
  const levelName = getDimensionLevelName(dimension, value);
  const levels = DIMENSION_LEVEL_NAMES[dimension];

  const handleValueChange = useCallback(
    ([next]: number[]) => {
      if (typeof next === "number") onChange(next);
    },
    [onChange],
  );

  const activeStep = Math.round(value * (STEP_COUNT - 1));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <span className="text-xs font-semibold text-primary">{levelName}</span>
      </div>

      <Slider
        min={DIMENSION_MIN}
        max={DIMENSION_MAX}
        step={DIMENSION_STEP}
        value={[value]}
        onValueChange={handleValueChange}
        disabled={disabled}
        aria-label={label}
        aria-valuemin={DIMENSION_MIN}
        aria-valuemax={DIMENSION_MAX}
        aria-valuenow={value}
        aria-valuetext={levelName}
      />

      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{low}</span>
        <div className="flex gap-[2px]" aria-hidden>
          {levels.map((levelLabel, idx) => (
            <div
              key={levelLabel}
              className={cn(
                "h-1 w-1 rounded-full transition-colors",
                idx === activeStep ? "bg-primary" : "bg-muted-foreground/30",
              )}
              title={levelLabel}
            />
          ))}
        </div>
        <span>{high}</span>
      </div>
    </div>
  );
}

export interface DimensionsFormProps {
  /** Profile ID is required to call PUT /{profileId}/dimensions. */
  profileId: string;
  /** Initial dimensions — defaults to 0.5 on every axis if omitted. */
  initial?: PersonalityDimensions;
  /** Called after a successful save with the persisted dimensions. */
  onSave?: (dimensions: PersonalityDimensions) => void;
  /** Whether the mutation is currently in flight (external control). */
  isPending?: boolean;
}

/**
 * Standalone dimensions editor for a `PersonalityProfile`. Renders 6
 * labeled sliders (energy, warmth, humor, expressiveness, narrative,
 * verbosity) snapped to 5 discrete steps (0, 0.25, …, 1). Shows an
 * explicit "Guardar dimensiones" button only when values have changed.
 *
 * Extracted from `DimensionSlidersAction` so it can be used both by the
 * action wrapper and by the new `DimensionsPanel` in the Estilo section.
 */
export function DimensionsForm({
  profileId,
  initial,
  onSave,
  isPending: externalPending,
}: DimensionsFormProps) {
  const [dims, setDims] = useState<PersonalityDimensions>(initial ?? DEFAULT_DIMENSIONS);
  const [isDirty, setIsDirty] = useState(false);
  const updateDimensions = useUpdateDimensions();

  const isPending = externalPending ?? updateDimensions.isPending;

  const handleChange = useCallback(
    (dim: keyof PersonalityDimensions) => (next: number) => {
      setDims((prev) => ({ ...prev, [dim]: next }));
      setIsDirty(true);
    },
    [],
  );

  const handleSave = useCallback(async () => {
    try {
      await updateDimensions.mutateAsync({ profileId, dimensions: dims });
      toast.success("Dimensiones guardadas.");
      setIsDirty(false);
      onSave?.(dims);
    } catch {
      toast.error("No se pudo guardar. Inténtalo de nuevo.");
    }
  }, [updateDimensions, profileId, dims, onSave]);

  return (
    <div className="space-y-6">
      <div className="space-y-5">
        {DIMENSION_ORDER.map((dim) => (
          <DimensionSliderRow
            key={dim}
            dimension={dim}
            value={dims[dim]}
            onChange={handleChange(dim)}
            disabled={isPending}
          />
        ))}
      </div>

      {isDirty && (
        <Button
          size="sm"
          onClick={handleSave}
          disabled={isPending}
          className="w-full sm:w-auto"
          aria-label="Guardar dimensiones"
        >
          {isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Save className="mr-2 h-4 w-4" aria-hidden />
          )}
          Guardar dimensiones
        </Button>
      )}
    </div>
  );
}
