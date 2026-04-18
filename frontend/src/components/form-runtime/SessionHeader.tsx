"use client";

import { Undo2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useFormRuntime } from "./FormRuntimeContext";

export interface SessionHeaderProps {
  /** Optional CTA to start a guided interview (copilot). */
  onStartInterview?: () => void;
  className?: string;
}

/**
 * Top bar: section title, completeness chip, "Entrevista guiada" CTA,
 * session-undo button. Replaces the old FocusBar + progress chip.
 */
export function SessionHeader({ onStartInterview, className }: SessionHeaderProps) {
  const { schema, values, isDirty, undoSession } = useFormRuntime();
  const { completed, total } = computeCompleteness(schema.fields, values);

  return (
    <header
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3",
        className,
      )}
    >
      <div className="min-w-0">
        <h2 className="truncate text-lg font-semibold">{schema.title}</h2>
        {schema.description && (
          <p className="truncate text-xs text-muted-foreground">{schema.description}</p>
        )}
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
