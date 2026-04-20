"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { CompletionDot, type CompletionState } from "./CompletionDot";
import { useFormRuntime } from "./FormRuntimeContext";

import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface FieldListProps {
  activeFieldId: string | null;
  /** Consumer-provided URL builder: given a field id, return the route to navigate to. */
  getFieldHref: (fieldId: string) => string;
  className?: string;
}

/**
 * Flat Finder-style field list: one row per field, completion dot + label +
 * chevron. Rows are Next.js Links so the active field lives in the URL and
 * browser back works. Rendered inside a FinderColumn by consumers.
 */
export function FieldList({ activeFieldId, getFieldHref, className }: FieldListProps) {
  const { schema, values } = useFormRuntime();

  return (
    <ul className={cn("flex flex-col", className)} role="listbox">
      {schema.fields.map((field) => (
        <FieldRow
          key={field.id}
          field={field}
          value={values[field.path]}
          isActive={field.id === activeFieldId}
          href={getFieldHref(field.id)}
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
}

function FieldRow({ field, value, isActive, href }: FieldRowProps) {
  const state: CompletionState = hasValue(value) ? "filled" : "empty";
  return (
    <li>
      <Link
        href={href}
        aria-selected={isActive}
        role="option"
        className={cn(
          "relative flex items-center gap-3 border-b border-border/50",
          "px-[14px] py-[9px] text-[13px] transition-colors",
          isActive ? "bg-muted/60" : "hover:bg-muted/30",
          isActive &&
            "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
        )}
      >
        <CompletionDot state={state} />
        <span className="min-w-0 flex-1 truncate text-foreground">{field.label}</span>
        <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
      </Link>
    </li>
  );
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  return true;
}
