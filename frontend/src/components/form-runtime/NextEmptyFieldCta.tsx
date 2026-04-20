"use client";

import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { useFormRuntime } from "./FormRuntimeContext";

import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface NextEmptyFieldCtaProps {
  getFieldHref: (fieldId: string) => string;
  className?: string;
}

/**
 * Floating CTA pinned at the bottom of the editor main area, below the
 * field grid. Two states:
 *   - Pending: dashed brand border + "Siguiente vacío · {Field} →".
 *   - Complete: solid success tint + "Sección completa".
 *
 * The empty field is computed from the runtime state; no external fetch
 * required.
 */
export function NextEmptyFieldCta({ getFieldHref, className }: NextEmptyFieldCtaProps) {
  const { schema, values } = useFormRuntime();
  const next = useMemo(() => findNextEmpty(schema.fields, values), [schema.fields, values]);

  if (!next) {
    return (
      <div
        className={cn(
          "mx-10 mb-6 flex max-w-[360px] items-center gap-2 rounded-md border border-[hsl(var(--success))]/40 bg-[hsl(var(--success))]/10 px-4 py-3 text-[13px] text-foreground",
          className,
        )}
        role="status"
      >
        <Check className="h-4 w-4 text-[hsl(var(--success))]" aria-hidden="true" />
        <span className="font-medium">Sección completa</span>
      </div>
    );
  }

  return (
    <Link
      href={getFieldHref(next.id)}
      className={cn(
        "group mx-10 mb-6 flex max-w-[360px] items-center gap-3 rounded-md border border-dashed border-brand/40 bg-brand/[0.08] px-4 py-3 text-[13px] transition-colors hover:bg-brand/[0.14]",
        className,
      )}
    >
      <ArrowRight className="h-4 w-4 shrink-0 text-brand" aria-hidden="true" />
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-muted-foreground">
          Siguiente vacío
        </span>
        <span className="truncate font-medium text-foreground">{next.label}</span>
      </div>
      <span className="text-brand" aria-hidden="true">
        ›
      </span>
    </Link>
  );
}

/**
 *
 */
export function findNextEmpty(
  fields: FieldSchema[],
  values: Record<string, unknown>,
): FieldSchema | null {
  for (const field of fields) {
    if (!hasValue(values[field.path])) return field;
  }
  return null;
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  return true;
}
