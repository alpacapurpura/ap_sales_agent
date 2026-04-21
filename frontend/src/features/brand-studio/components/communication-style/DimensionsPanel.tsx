"use client";

import { Pencil, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DIMENSION_LABELS,
  getDimensionLevelName,
  type PersonalityDimensions,
} from "@/features/brand-studio/types/personality";
import { cn } from "@/lib/utils";

import { DimensionsForm } from "./DimensionsForm";

const DIMENSION_ORDER: (keyof PersonalityDimensions)[] = [
  "energy",
  "warmth",
  "humor",
  "expressiveness",
  "narrative",
  "verbosity",
];

interface DimensionReadRowProps {
  dimension: keyof PersonalityDimensions;
  value: number;
}

function DimensionReadRow({ dimension, value }: DimensionReadRowProps) {
  const { label, low, high } = DIMENSION_LABELS[dimension];
  const levelName = getDimensionLevelName(dimension, value);
  const steps = [0, 0.25, 0.5, 0.75, 1];
  const activeStep = Math.round(value * 4);

  return (
    <div className="flex items-center gap-3 text-[13px]">
      <span className="w-28 flex-shrink-0 text-muted-foreground">{label}</span>
      <span className="w-16 flex-shrink-0 text-xs text-muted-foreground/60">{low}</span>
      <div className="flex flex-1 items-center gap-[3px]" aria-hidden>
        {steps.map((_, idx) => (
          <div
            key={idx}
            className={cn(
              "h-2 flex-1 rounded-full transition-colors",
              idx === activeStep ? "bg-primary" : "bg-muted",
            )}
          />
        ))}
      </div>
      <span className="w-16 flex-shrink-0 text-right text-xs text-muted-foreground/60">{high}</span>
      <span className="w-24 flex-shrink-0 text-right text-xs font-semibold text-primary">
        {levelName}
      </span>
    </div>
  );
}

interface DimensionsPanelProps {
  profileId: string;
  dimensions: PersonalityDimensions;
  onSaved?: (dims: PersonalityDimensions) => void;
}

/**
 * Displays the 6 personality dimensions. Default mode is read-only with a
 * compact visual representation. "Editar" button switches to the full
 * `DimensionsForm` with interactive sliders and explicit save.
 */
export function DimensionsPanel({ profileId, dimensions, onSaved }: DimensionsPanelProps) {
  const [editMode, setEditMode] = useState(false);

  const handleSaved = (dims: PersonalityDimensions) => {
    setEditMode(false);
    onSaved?.(dims);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Dimensiones
        </p>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setEditMode((prev) => !prev)}
          className="h-7 gap-1 px-2 text-xs"
          aria-label={editMode ? "Cancelar edición de dimensiones" : "Editar dimensiones"}
        >
          {editMode ? (
            <>
              <X className="h-3 w-3" aria-hidden />
              Cancelar
            </>
          ) : (
            <>
              <Pencil className="h-3 w-3" aria-hidden />
              Editar
            </>
          )}
        </Button>
      </div>

      {editMode ? (
        <div className="rounded-lg border border-border bg-card/50 p-4">
          <DimensionsForm profileId={profileId} initial={dimensions} onSave={handleSaved} />
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card/50 px-4 py-3 space-y-2">
          {DIMENSION_ORDER.map((dim) => (
            <DimensionReadRow key={dim} dimension={dim} value={dimensions[dim]} />
          ))}
        </div>
      )}
    </div>
  );
}
