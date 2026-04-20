"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { inferFieldLayout, layoutToColSpanClass } from "@/lib/form-runtime/schema";
import { cn } from "@/lib/utils";

import { AutosaveBanner } from "./AutosaveBanner";
import { EditableField } from "./EditableField";
import { useFormRuntime } from "./FormRuntimeContext";

export interface FieldDetailProps {
  activeFieldId: string | null;
  /** Href to return to the list view (mobile back affordance). */
  backHref?: string;
  /** When true, render as a full-screen overlay (mobile <768px). */
  fullScreen?: boolean;
  className?: string;
}

/**
 * Editor area — renders ALL schema fields inside a responsive grid.
 * ``activeFieldId`` (derived from the URL) scrolls the matching field into
 * view and focuses it — the field list column acts as a navigational anchor,
 * not a filter.
 *
 * Grid breakpoints (UI-SPEC §4):
 *   <900px       → 1 col
 *   900–1499px   → 2 cols
 *   ≥1500px      → 3 cols
 *
 * Per-field width hint comes from ``field.layout`` (default inferred from
 * field.type via ``inferFieldLayout``).
 */
export function FieldDetail({ activeFieldId, backHref, fullScreen, className }: FieldDetailProps) {
  const { schema, autosaveStatus, autosaveError } = useFormRuntime();
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!activeFieldId || !scrollRef.current) return;
    const el = scrollRef.current.querySelector<HTMLElement>(
      `[data-field-anchor="${activeFieldId}"]`,
    );
    if (el) {
      el.scrollIntoView({ block: "start", behavior: "smooth" });
      const focusable = el.querySelector<HTMLElement>(
        "textarea, input:not([type=hidden]), [role=button], button",
      );
      focusable?.focus({ preventScroll: true });
    }
  }, [activeFieldId]);

  return (
    <div
      ref={scrollRef}
      className={cn(
        "relative flex min-h-0 min-w-0 flex-1 flex-col",
        fullScreen && "fixed inset-0 z-40 bg-background",
        className,
      )}
      aria-label="Editor de campos"
    >
      {fullScreen && backHref && (
        <Button type="button" variant="ghost" size="sm" asChild className="m-2 self-start">
          <Link href={backHref}>
            <ChevronLeft className="mr-1 h-4 w-4" />
            Atrás
          </Link>
        </Button>
      )}

      {autosaveStatus && (
        <div className="shrink-0 px-10 pt-4">
          <AutosaveBanner status={autosaveStatus} error={autosaveError ?? null} />
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-10 pb-10 pt-7">
        <div className="grid w-full grid-cols-1 gap-x-[var(--brand-field-grid-gap-col)] gap-y-[var(--brand-field-grid-gap-row)] md:grid-cols-2 xl:grid-cols-3">
          {schema.fields.map((field) => {
            const layout = inferFieldLayout(field);
            return (
              <div
                key={field.id}
                data-field-anchor={field.id}
                className={cn(
                  "scroll-mt-4",
                  layoutToColSpanClass(layout),
                  activeFieldId === field.id &&
                    "rounded-md ring-2 ring-ring/30 ring-offset-2 ring-offset-background",
                )}
              >
                <EditableField field={field} autoFocus={activeFieldId === field.id} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
