import { cn } from "@/lib/utils";

import type { ReactNode } from "react";

export interface FinderColumnProps {
  /** Uppercase heading shown in the 44px header. */
  title: string;
  /** Optional count/status chip rendered to the right of the title. */
  count?: number | string;
  /** Optional custom node replacing the count (autosave status, chip, etc.). */
  headerTrailing?: ReactNode;
  /** Body content — scrolls independently. */
  children: ReactNode;
  /** Tailwind width class (e.g. "w-[260px]"). Omit for flex-1. */
  widthClass?: string;
  /** Optional background class for depth gradient between columns. */
  bgClass?: string;
  /** ARIA label for assistive tech. */
  ariaLabel?: string;
  className?: string;
}

/**
 * Shared Finder-style column primitive. Header is 44px, uppercase label,
 * optional count/status chip on the right. Body is flex-1 with independent
 * scroll. Used by sections nav, fields list, instance picker and editor.
 *
 * Width is fixed via `widthClass`; omit to flex-1 (used for the editor).
 * Follows UI-SPEC-locked-dimensions.md §1–2.
 */
export function FinderColumn({
  title,
  count,
  headerTrailing,
  children,
  widthClass,
  bgClass,
  ariaLabel,
  className,
}: FinderColumnProps) {
  return (
    <section
      aria-label={ariaLabel ?? title}
      className={cn(
        "flex min-h-0 min-w-0 flex-col border-r border-border last:border-r-0",
        widthClass ?? "flex-1",
        bgClass,
        className,
      )}
    >
      <header
        className={cn(
          "flex h-[var(--brand-col-header-h)] shrink-0 items-center justify-between",
          "border-b border-border px-4",
        )}
      >
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          {title}
        </h3>
        {headerTrailing ??
          (count !== undefined ? (
            <span className="text-[11px] text-muted-foreground">{count}</span>
          ) : null)}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </section>
  );
}
