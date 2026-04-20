"use client";

import { Check } from "lucide-react";
import { createElement, forwardRef } from "react";

import { Card } from "@/components/ui/card";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { cn } from "@/lib/utils";

import type { BusinessTypeMetadataDTO } from "../types/tenant-profile";

interface BusinessTypeCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Catalog metadata for this card. */
  metadata: BusinessTypeMetadataDTO;
  /** Whether this card is currently selected. */
  isSelected: boolean;
  /** Whether this card should be disabled (max selection reached). */
  isDisabled?: boolean;
  /** Compact mode reduces padding for tighter layouts. */
  compact?: boolean;
}

/**
 * Single selectable card for a business type.
 *
 * Displays icon + label_es + description_es + first example.
 * Selected/disabled states are controlled externally by BusinessTypesSelector.
 *
 * CONTRACT §6.1 — components/BusinessTypeCard.tsx
 */
export const BusinessTypeCard = forwardRef<HTMLDivElement, BusinessTypeCardProps>(
  ({ metadata, isSelected, isDisabled = false, compact = false, className, ...props }, ref) => {
    const iconComponent = resolveIconByName(metadata.icon_name);

    return (
      <Card
        ref={ref}
        role="button"
        aria-pressed={isSelected}
        aria-disabled={isDisabled}
        tabIndex={isDisabled ? -1 : 0}
        className={cn(
          "cursor-pointer transition border-2 select-none",
          compact ? "p-3" : "p-4",
          isSelected && !isDisabled
            ? "border-primary bg-primary/5 shadow-sm"
            : "border-border hover:border-primary/40",
          isDisabled && !isSelected && "opacity-40 cursor-not-allowed pointer-events-none",
          className,
        )}
        {...props}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div
              className={cn(
                "shrink-0 h-9 w-9 rounded-md flex items-center justify-center",
                isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-foreground/80",
              )}
            >
              {createElement(iconComponent, { className: "h-4 w-4", "aria-hidden": true })}
            </div>
            <div className="flex-1 min-w-0 space-y-1">
              <div className="font-semibold text-sm">{metadata.label_es}</div>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {metadata.description_es}
              </p>
              {!compact && metadata.examples_es.length > 0 && (
                <ul className="text-[10px] text-muted-foreground space-y-0.5 mt-1">
                  {metadata.examples_es.slice(0, 2).map((ex) => (
                    <li key={ex} className="truncate">
                      {ex}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          {isSelected && <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" aria-hidden />}
        </div>
      </Card>
    );
  },
);
BusinessTypeCard.displayName = "BusinessTypeCard";
