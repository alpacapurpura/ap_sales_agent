"use client";

import { Loader2, Save } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useUpdateDimensions } from "../../api/personality";
import {
  DIMENSION_LABELS,
  DIMENSION_LEVEL_NAMES,
  getDimensionLevelName,
} from "../../types/personality";

import type { PersonalityDimensions } from "../../types/personality";

const DIMENSION_ORDER: (keyof PersonalityDimensions)[] = [
  "energy",
  "warmth",
  "humor",
  "expressiveness",
  "narrative",
  "verbosity",
];

// Simple 5-step slider using input[type=range]
function DimensionSlider({
  dimension,
  value,
  onChange,
}: {
  dimension: keyof PersonalityDimensions;
  value: number;
  onChange: (val: number) => void;
}) {
  const { label, low, high } = DIMENSION_LABELS[dimension];
  const levelName = getDimensionLevelName(dimension, value);
  const levels = DIMENSION_LEVEL_NAMES[dimension];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        <span className="text-xs font-semibold text-primary">{levelName}</span>
      </div>

      {/* Range input */}
      <input
        type="range"
        min={0}
        max={1}
        step={0.25}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className={cn(
          "w-full h-2 rounded-full appearance-none cursor-pointer",
          "bg-muted [&::-webkit-slider-thumb]:appearance-none",
          "[&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4",
          "[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary",
          "[&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-md",
          "[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4",
          "[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary",
          "[&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer",
        )}
      />

      {/* Low/high labels + step markers */}
      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{low}</span>
        <div className="flex gap-[1px]">
          {levels.map((lvl, i) => (
            <div
              key={i}
              className={cn(
                "w-1 h-1 rounded-full transition-colors",
                Math.round(value * 4) === i ? "bg-primary" : "bg-muted-foreground/30",
              )}
              title={lvl}
            />
          ))}
        </div>
        <span>{high}</span>
      </div>
    </div>
  );
}

interface DimensionSlidersProps {
  initialDimensions: PersonalityDimensions;
}

export function DimensionSliders({ initialDimensions }: DimensionSlidersProps) {
  const [dims, setDims] = useState<PersonalityDimensions>(initialDimensions);
  const [isDirty, setIsDirty] = useState(false);
  const updateDimensions = useUpdateDimensions();

  const handleChange = (dim: keyof PersonalityDimensions, val: number) => {
    setDims((prev) => ({ ...prev, [dim]: val }));
    setIsDirty(true);
  };

  const handleSave = async () => {
    try {
      await updateDimensions.mutateAsync(dims);
      toast.success("Dimensiones guardadas.");
      setIsDirty(false);
    } catch {
      toast.error("No se pudo guardar. Inténtalo de nuevo.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-5">
        {DIMENSION_ORDER.map((dim) => (
          <DimensionSlider
            key={dim}
            dimension={dim}
            value={dims[dim]}
            onChange={(val) => handleChange(dim, val)}
          />
        ))}
      </div>

      {isDirty && (
        <Button
          size="sm"
          onClick={() => void handleSave()}
          disabled={updateDimensions.isPending}
          className="w-full sm:w-auto"
        >
          {updateDimensions.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Guardar dimensiones
        </Button>
      )}
    </div>
  );
}
