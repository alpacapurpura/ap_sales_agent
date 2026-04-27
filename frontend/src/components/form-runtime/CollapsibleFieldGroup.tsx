"use client";

import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

import type { FieldSchema } from "@/lib/form-runtime/schema";

/**
 * Bucket of fields sharing the same `field.group`. Order is preserved from
 * the source schema so the runtime layout is deterministic.
 */
export interface FieldGroupBucket {
  /** Group label declared in the schema. `null` = ungrouped tail/head. */
  readonly group: string | null;
  readonly fields: readonly FieldSchema[];
}

/**
 * Bucket adjacent fields by `field.group`. Consecutive entries that share a
 * label collapse into a single bucket; ungrouped fields fall into a `null`
 * bucket. Schemas without any `group` declared therefore produce a single
 * `null` bucket — callers can detect this and skip the collapsible header.
 */
interface MutableBucket {
  group: string | null;
  fields: FieldSchema[];
}

/**
 *
 */
export function groupFieldsByGroup(fields: readonly FieldSchema[]): readonly FieldGroupBucket[] {
  const buckets: MutableBucket[] = [];
  for (const field of fields) {
    const groupLabel: string | null = field.group ?? null;
    const last = buckets[buckets.length - 1];
    if (last?.group !== groupLabel) {
      buckets.push({ group: groupLabel, fields: [field] });
    } else {
      last.fields.push(field);
    }
  }
  return buckets;
}

/** True when at least one bucket has a non-null group label. */
export function hasFieldGroups(buckets: readonly FieldGroupBucket[]): boolean {
  return buckets.some((bucket) => bucket.group !== null);
}

export interface CollapsibleFieldGroupProps {
  /** Group label rendered in the header. */
  label: string;
  /** Optional count chip rendered next to the label (e.g. number of fields). */
  count?: number;
  /** Initial expanded state. Defaults to `true` — groups read like sections, and
   *  hiding everything by default would surprise users. */
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
}

/**
 * Wraps a bucket of fields with a clickable header that collapses/expands
 * the bucket. Built on top of Radix's `Collapsible` primitive so animation
 * and keyboard semantics match the rest of the design system.
 *
 * Generic by design — works with both top-level section fields
 * (`FieldDetail`) and array-item sub-fields (`ArrayCardsEditor`,
 * `ArraySplitEditor`). State is local; persistence is intentionally out of
 * scope (the panel is short-lived and the user expectation is "expand on
 * mount").
 */
export function CollapsibleFieldGroup({
  label,
  count,
  defaultOpen = true,
  children,
  className,
}: CollapsibleFieldGroupProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Collapsible
      open={open}
      onOpenChange={setOpen}
      className={cn("rounded-lg border border-border/60 bg-muted/20", className)}
    >
      <CollapsibleTrigger
        className={cn(
          "flex w-full items-center justify-between gap-2 px-3 py-2 text-left",
          "text-[11px] font-semibold uppercase tracking-wider text-muted-foreground",
          "transition-colors hover:bg-muted/40",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
      >
        <span className="flex items-center gap-2">
          {label}
          {typeof count === "number" && (
            <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-normal normal-case text-muted-foreground">
              {count}
            </span>
          )}
        </span>
        <ChevronDown
          className={cn("h-3.5 w-3.5 transition-transform", open ? "rotate-0" : "-rotate-90")}
          aria-hidden
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="px-3 pb-3 pt-1 data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
        <div className="space-y-3">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}
