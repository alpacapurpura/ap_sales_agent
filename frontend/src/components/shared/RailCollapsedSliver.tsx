"use client";

import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

export interface RailCollapsedSliverProps {
  /** Vertical label shown in the sliver. Ej: "Variantes (3)", "Secciones". */
  label: string;
  /** ARIA label for the expand button. */
  ariaLabel: string;
  /** Click handler — toggles the rail back to its expanded state. */
  onExpand: () => void;
  className?: string;
}

/**
 * Thin vertical bar that replaces a collapsed rail (variants, sections, …).
 * Stays visible so the user can re-expand the rail with a single click —
 * collapsing the rail down to ``null`` made it disappear with no affordance
 * to recover.
 *
 * Width matches the topbar/sidebar density of the offer-studio shell
 * (32px) so the layout shift on collapse/expand is just the rail width
 * minus the sliver.
 */
export function RailCollapsedSliver({
  label,
  ariaLabel,
  onExpand,
  className,
}: RailCollapsedSliverProps) {
  return (
    <button
      type="button"
      onClick={onExpand}
      aria-label={ariaLabel}
      title={ariaLabel}
      className={cn(
        "group flex w-8 shrink-0 flex-col items-center gap-3 border-r bg-background py-3 text-muted-foreground hover:bg-muted hover:text-foreground",
        className,
      )}
    >
      <ChevronRight
        className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
        aria-hidden
      />
      <span
        className="text-[10px] font-semibold uppercase tracking-wider"
        style={{ writingMode: "vertical-rl" }}
      >
        {label}
      </span>
    </button>
  );
}
