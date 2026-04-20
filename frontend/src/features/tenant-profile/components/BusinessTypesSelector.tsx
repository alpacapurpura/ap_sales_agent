"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

import { useBusinessTypesCatalog } from "../hooks/use-business-types-catalog";

import { BusinessTypeCard } from "./BusinessTypeCard";

import type { ExpertBusinessTypeSlug } from "../types/tenant-profile";

interface BusinessTypesSelectorProps {
  /** Currently selected slugs. */
  value: ExpertBusinessTypeSlug[];
  /** Called with the new selection after a toggle. */
  onChange: (value: ExpertBusinessTypeSlug[]) => void;
  /** Minimum required selections. Defaults to 1. */
  min?: number;
  /** Maximum allowed selections. Defaults to 2. */
  max?: number;
  /** Compact card mode. */
  compact?: boolean;
}

/**
 * Grid of 9 selectable BusinessTypeCard components.
 *
 * Enforces min/max constraints:
 * - When max is reached, unselected cards are disabled with a tooltip.
 * - A helper text below the grid shows the current constraint state.
 *
 * CONTRACT §6.1 — components/BusinessTypesSelector.tsx
 */
export function BusinessTypesSelector({
  value,
  onChange,
  min = 1,
  max = 2,
  compact = false,
}: BusinessTypesSelectorProps) {
  const { data, isLoading } = useBusinessTypesCatalog();
  const selected = new Set<ExpertBusinessTypeSlug>(value);
  const maxReached = selected.size >= max;

  const toggle = (slug: ExpertBusinessTypeSlug) => {
    const next = new Set(selected);
    if (next.has(slug)) {
      next.delete(slug);
    } else if (!maxReached) {
      next.add(slug);
    }
    onChange(Array.from(next));
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-28 bg-muted/50 animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  const helperText =
    selected.size === 0
      ? `Elige entre ${min} y ${max} opciones.`
      : selected.size === max
        ? `Seleccionaste el máximo (${max}). Deselecciona uno para cambiar.`
        : `${selected.size} seleccionado${selected.size === 1 ? "" : "s"} · Elige hasta ${max}.`;

  return (
    <TooltipProvider>
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">{helperText}</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(data?.business_types ?? []).map((meta) => {
            const isSelected = selected.has(meta.slug);
            const isDisabled = maxReached && !isSelected;

            if (isDisabled) {
              return (
                <Tooltip key={meta.slug}>
                  <TooltipTrigger asChild>
                    <div>
                      <BusinessTypeCard
                        metadata={meta}
                        isSelected={false}
                        isDisabled
                        compact={compact}
                      />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top">
                    <p>Ya elegiste el máximo de {max} tipos. Deselecciona uno para cambiar.</p>
                  </TooltipContent>
                </Tooltip>
              );
            }

            return (
              <BusinessTypeCard
                key={meta.slug}
                metadata={meta}
                isSelected={isSelected}
                compact={compact}
                onClick={() => toggle(meta.slug)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    toggle(meta.slug);
                  }
                }}
              />
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
}
