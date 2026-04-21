"use client";

import { type ReactNode } from "react";

import { ArrayCardsEditor } from "./array/ArrayCardsEditor";
import { ArraySplitEditor } from "./array/ArraySplitEditor";

import type { BaseInputProps } from "./types";
import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

/**
 * Renderer injected by the parent FieldRenderer so ArrayInput can render
 * nested fields without a direct import dependency (breaks the import cycle).
 */
export type NestedFieldRenderer = (props: {
  field: FieldSchema;
  value: unknown;
  onChange: (next: unknown) => void;
  disabled?: boolean;
}) => ReactNode;

export interface ArrayInputProps extends BaseInputProps<Row[] | null | undefined> {
  renderField: NestedFieldRenderer;
}

/**
 * Dispatcher — selects the render mode automatically based on itemSchema.fields.length:
 *
 * - <= 3 fields  → "cards"  (Variante A — Enhanced Cards)
 * - >= 4 fields  → "split"  (Variante C — Split Master-Detail)
 *
 * Schema can override via renderAs: "cards" | "split" | "accordion".
 * Accordion mode falls through to cards (Sprint siguiente).
 *
 * See .claude/rules/form-runtime-array.md
 */
export function ArrayInput({ field, value, onChange, disabled, renderField }: ArrayInputProps) {
  if (!field.itemSchema) {
    return (
      <div className="text-xs text-destructive">
        Schema error: array field &quot;{field.id}&quot; missing itemSchema
      </div>
    );
  }

  const mode = resolveMode(field);

  if (mode === "split") {
    return (
      <ArraySplitEditor
        field={field}
        value={value}
        onChange={onChange}
        renderField={renderField}
        disabled={disabled}
      />
    );
  }

  // "cards" and "accordion" (future) both use cards editor for now
  return (
    <ArrayCardsEditor
      field={field}
      value={value}
      onChange={onChange}
      renderField={renderField}
      disabled={disabled}
    />
  );
}

/**
 * Resolves the render mode for an array field.
 * Exported for testability.
 */
export function resolveMode(field: FieldSchema): "cards" | "split" | "accordion" {
  if (field.renderAs) return field.renderAs;
  const len = field.itemSchema?.fields.length ?? 0;
  return len >= 4 ? "split" : "cards";
}
