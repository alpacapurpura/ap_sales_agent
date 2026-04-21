"use client";

import { ChevronRight } from "lucide-react";

import { useActiveField } from "@/lib/form-runtime/hooks";
import { cn } from "@/lib/utils";

import { CompletionDot, type CompletionState } from "./CompletionDot";
import { useFormRuntime } from "./FormRuntimeContext";

import type { FieldSchema } from "@/lib/form-runtime/schema";
import type { MouseEvent } from "react";

export interface FieldListProps {
  activeFieldId: string | null;
  /** Consumer-provided URL builder: given a field id, return the route to navigate to. */
  getFieldHref: (fieldId: string) => string;
  className?: string;
}

/**
 * Flat Finder-style field list: one row per field, completion dot + label +
 * chevron. Rows are anchor elements so right-click-to-copy works and the
 * URL is shareable, but a click is intercepted and resolved client-side
 * via ``setActiveField`` — no Next.js navigation, no RSC fetch.
 */
export function FieldList({ activeFieldId, getFieldHref, className }: FieldListProps) {
  const { schema, values } = useFormRuntime();
  const { setActiveField } = useActiveField();

  return (
    <ul className={cn("flex flex-col", className)} role="listbox">
      {schema.fields.map((field) => (
        <FieldRow
          key={field.id}
          field={field}
          value={values[field.path]}
          isActive={field.id === activeFieldId}
          href={getFieldHref(field.id)}
          onSelect={() => setActiveField(field.id)}
        />
      ))}
    </ul>
  );
}

interface FieldRowProps {
  field: FieldSchema;
  value: unknown;
  isActive: boolean;
  href: string;
  onSelect: () => void;
}

function FieldRow({ field, value, isActive, href, onSelect }: FieldRowProps) {
  const state: CompletionState = hasValue(value) ? "filled" : "empty";

  function handleClick(ev: MouseEvent<HTMLAnchorElement>) {
    // Let the browser handle modified clicks (ctrl/cmd/middle — open in
    // new tab), right-click, and anything that is not a plain primary
    // click. Everything else resolves client-side.
    if (ev.defaultPrevented) return;
    if (ev.button !== 0) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    ev.preventDefault();
    onSelect();
  }

  return (
    <li>
      <a
        href={href}
        onClick={handleClick}
        aria-selected={isActive}
        role="option"
        className={cn(
          "relative flex items-center gap-3 border-b border-border/50",
          "px-[14px] py-[9px] text-[13px] transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          isActive ? "bg-muted/60" : "hover:bg-muted/30",
          isActive &&
            "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
        )}
      >
        <CompletionDot state={state} />
        <span className="min-w-0 flex-1 truncate text-foreground">{field.label}</span>
        <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
      </a>
    </li>
  );
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  return true;
}
