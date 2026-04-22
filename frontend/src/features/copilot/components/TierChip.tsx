import { forwardRef } from "react";

import { cn } from "@/lib/utils";

import type { ModelTier } from "../types/conversations";

// ── Types ────────────────────────────────────────────────────────────

interface TierChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  tier: ModelTier;
  size?: "sm" | "xs";
}

// ── Config ───────────────────────────────────────────────────────────

const TIER_CONFIG: Record<ModelTier, { colorClass: string; label: string }> = {
  nano: { colorClass: "bg-green-100 text-green-800", label: "nano" },
  mini: { colorClass: "bg-blue-100 text-blue-800", label: "mini" },
  reasoning: { colorClass: "bg-amber-100 text-amber-800", label: "o4" },
  heavy: { colorClass: "bg-red-100 text-red-800", label: "o3" },
};

// ── Component ────────────────────────────────────────────────────────

/**
 * Small colored badge indicating the AI model tier used for a message.
 * Pure display component — no hooks, server-compatible.
 */
export const TierChip = forwardRef<HTMLSpanElement, TierChipProps>(
  ({ tier, size = "xs", className, ...props }, ref) => {
    const { colorClass, label } = TIER_CONFIG[tier];

    return (
      <span
        ref={ref}
        title={`Modelo: ${tier}`}
        className={cn(
          "inline-flex items-center font-mono font-medium tracking-tight rounded-full",
          colorClass,
          size === "xs" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-0.5",
          className,
        )}
        {...props}
      >
        {label}
      </span>
    );
  },
);
TierChip.displayName = "TierChip";
