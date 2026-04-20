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

import type { ActionComponentProps } from "@/lib/form-runtime/actions";

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

const DEFAULT_DIMENSIONS: PersonalityDimensions = {
  energy: 0.5,
  warmth: 0.5,
  humor: 0.5,
  expressiveness: 0.5,
  narrative: 0.5,
  verbosity: 0.5,
};

interface DimensionSliderProps {
  dimension: keyof PersonalityDimensions;
  value: number;
  onChange: (val: number) => void;
}

function DimensionSlider({ dimension, value, onChange }: DimensionSliderProps) {
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
        aria-label={label}
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

/**
 * DimensionSliders action — fine-tunes the personality profile's 6
 * dimensions (energy, warmth, humor, expressiveness, narrative, verbosity).
 * Each slider is a shadcn Slider snapped to 5 discrete steps (0, 0.25, …, 1).
 *
 * Local state tracks edits; `Guardar dimensiones` fires the backend mutation
 * and, on success, bubbles the new dimensions via `onChange` so the form-runtime
 * mirrors the persisted value. Explicit save (not autosave) because the
 * backend mutation is authoritative and cache invalidation happens there.
 */
export function DimensionSlidersAction({
  value,
  onChange,
}: ActionComponentProps<PersonalityDimensions | null>) {
  const initial = value ?? DEFAULT_DIMENSIONS;
  const [dims, setDims] = useState<PersonalityDimensions>(initial);
  const [isDirty, setIsDirty] = useState(false);
  const updateDimensions = useUpdateDimensions();

  const handleChange = useCallback(
    (dim: keyof PersonalityDimensions) => (next: number) => {
      setDims((prev) => ({ ...prev, [dim]: next }));
      setIsDirty(true);
    },
    [],
  );

  const handleSave = useCallback(async () => {
    try {
      await updateDimensions.mutateAsync(dims);
      toast.success("Dimensiones guardadas.");
      setIsDirty(false);
      onChange(dims);
    } catch {
      toast.error("No se pudo guardar. Inténtalo de nuevo.");
    }
  }, [updateDimensions, dims, onChange]);

  return (
    <div className="space-y-6">
      <div className="space-y-5">
        {DIMENSION_ORDER.map((dim) => (
          <DimensionSlider
            key={dim}
            dimension={dim}
            value={dims[dim]}
            onChange={handleChange(dim)}
          />
        ))}
      </div>

      {isDirty && (
        <Button
          size="sm"
          onClick={handleSave}
          disabled={updateDimensions.isPending}
          className="w-full sm:w-auto"
        >
          {updateDimensions.isPending ? (
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
