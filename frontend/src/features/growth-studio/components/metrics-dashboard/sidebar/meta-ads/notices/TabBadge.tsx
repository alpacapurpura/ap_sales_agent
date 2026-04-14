"use client";

import { cn } from "@/lib/utils";
import type { NoticeSeverity } from "./types";

interface TabBadgeProps {
  count: number;
  severity: NoticeSeverity | null;
  className?: string;
}

/**
 * Small pill rendered next to a TabsTrigger label to signal pending notices.
 *
 * - Hidden when count is 0 (caller decides — we also return null as a safety).
 * - Color by severity (red critical / amber warning / blue info).
 * - Caps at "9+" to keep the tab list tidy.
 */
export function TabBadge({ count, severity, className }: TabBadgeProps) {
  if (count <= 0) return null;

  const color = (() => {
    switch (severity) {
      case "critical":
        return "bg-red-500/20 text-red-400 border-red-500/40";
      case "warning":
        return "bg-amber-500/20 text-amber-400 border-amber-500/40";
      case "info":
      default:
        return "bg-blue-500/20 text-blue-400 border-blue-500/40";
    }
  })();

  const label = count > 9 ? "9+" : String(count);

  return (
    <span
      className={cn(
        "ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full border px-1 text-[10px] font-semibold tabular-nums",
        color,
        className,
      )}
      aria-label={`${count} pendientes`}
    >
      {label}
    </span>
  );
}
