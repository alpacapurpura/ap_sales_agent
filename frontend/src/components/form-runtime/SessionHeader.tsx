"use client";

import { Undo2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useFormRuntime } from "./FormRuntimeContext";

export interface SessionHeaderProps {
  /** Optional CTA to start a guided interview (copilot). */
  onStartInterview?: () => void;
  /**
   * Override the section title resolved from schema. Offer-studio passes
   * the title from the backend SectionCatalog so the copy stays in a
   * single source of truth instead of being duplicated on each schema
   * file.
   */
  titleOverride?: string;
  /** Override the section description (same rationale as titleOverride). */
  descriptionOverride?: string;
  className?: string;
}

/**
 * Top bar: section title, completeness chip, "Entrevista guiada" CTA,
 * session-undo button. Replaces the old FocusBar + progress chip.
 *
 * Title + description can be provided via props (preferred — resolved
 * from the backend catalog) or fall back to the schema declarations
 * (legacy consumers that still hardcode copy inline).
 */
export function SessionHeader({
  onStartInterview,
  titleOverride,
  descriptionOverride,
  className,
}: SessionHeaderProps) {
  const { schema, values, isDirty, undoSession } = useFormRuntime();
  const { completed, total } = computeCompleteness(schema.fields, values);
  const title = titleOverride ?? schema.title ?? "";
  const description = descriptionOverride ?? schema.description ?? "";

  return (
    <header
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3",
        className,
      )}
    >
      <div className="min-w-0">
        {title && <h2 className="truncate text-lg font-semibold">{title}</h2>}
        {description && <p className="truncate text-xs text-muted-foreground">{description}</p>}
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="secondary" aria-label={`${completed} de ${total} campos completos`}>
          {completed}/{total}
        </Badge>
        {onStartInterview && (
          <Button type="button" variant="outline" size="sm" onClick={onStartInterview}>
            Entrevista guiada
          </Button>
        )}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={undoSession}
          disabled={!isDirty}
          aria-label="Deshacer cambios de la sesión"
        >
          <Undo2 className="mr-1 h-4 w-4" />
          Deshacer
        </Button>
      </div>
    </header>
  );
}

function computeCompleteness(
  fields: { id: string; path: string; required?: boolean }[],
  values: Record<string, unknown>,
): { completed: number; total: number } {
  const total = fields.length;
  let completed = 0;
  for (const field of fields) {
    if (hasValue(values[field.path])) completed += 1;
  }
  return { completed, total };
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  return true;
}
