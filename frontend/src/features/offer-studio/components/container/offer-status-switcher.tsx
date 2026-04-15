"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { canTransition } from "../../types/lifecycle";

import type { OfferLifecycleStatus } from "../../types/enums";

export interface OfferStatusSwitcherProps {
  currentStatus: OfferLifecycleStatus;
  /** Called when the user clicks a *different* pill. Modal confirmation
   *  is handled by the parent. */
  onTransitionRequested: (target: OfferLifecycleStatus) => void;
  /** Disable all pills (e.g. during in-flight mutation). */
  disabled?: boolean;
}

interface PillConfig {
  status: OfferLifecycleStatus;
  label: string;
  tooltip: string;
  activeClass: string;
}

const PILLS: PillConfig[] = [
  {
    status: "draft",
    label: "Borrador",
    tooltip: "La oferta no es visible para el Sales Agent. Podés editarla libremente.",
    activeClass: "bg-warning/20 text-warning border-warning/40",
  },
  {
    status: "active",
    label: "Activa",
    tooltip: "El Sales Agent la propone en conversaciones. La landing se sincroniza.",
    activeClass: "bg-success/20 text-success border-success/40",
  },
  {
    status: "paused",
    label: "Pausada",
    tooltip: "El Sales Agent deja de proponerla pero la reconoce si un cliente la menciona.",
    activeClass: "bg-muted text-foreground border-muted-foreground/40",
  },
];

/**
 * Segmented control with 3 lifecycle pills (archived is handled outside via the kebab menu).
 *
 * - Clicking the current pill is a no-op.
 * - Clicking a disallowed transition (e.g. draft → paused) is disabled upstream
 *   via `LIFECYCLE_TRANSITIONS`.
 * - Archived offers disable the whole switcher (restore lives in the archived panel).
 */
export function OfferStatusSwitcher({
  currentStatus,
  onTransitionRequested,
  disabled = false,
}: OfferStatusSwitcherProps) {
  const isArchived = currentStatus === "archived";

  return (
    <TooltipProvider delayDuration={200}>
      <div
        role="tablist"
        aria-label="Estado de la oferta"
        className={cn(
          "inline-flex items-center gap-1 rounded-lg border bg-card/50 p-1",
          isArchived && "opacity-60",
        )}
      >
        {PILLS.map((pill) => {
          const isSelected = pill.status === currentStatus;
          const allowed = !isArchived && canTransition(currentStatus, pill.status);
          const pillDisabled = disabled || isArchived || (!isSelected && !allowed);

          const button = (
            <button
              key={pill.status}
              type="button"
              role="tab"
              aria-selected={isSelected}
              disabled={pillDisabled}
              onClick={() => {
                if (isSelected || pillDisabled) return;
                onTransitionRequested(pill.status);
              }}
              className={cn(
                "h-7 rounded-md border border-transparent px-3 text-xs font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                "disabled:cursor-not-allowed disabled:opacity-50",
                isSelected
                  ? pill.activeClass
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {pill.label}
            </button>
          );

          return (
            <Tooltip key={pill.status}>
              <TooltipTrigger asChild>{button}</TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="max-w-xs text-xs">
                  {isArchived
                    ? "Oferta archivada. Usá 'Restaurar' en el panel de archivadas."
                    : pill.tooltip}
                </p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
