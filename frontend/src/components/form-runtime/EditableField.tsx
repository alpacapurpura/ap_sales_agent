"use client";

import { Label } from "@/components/ui/label";
import { useActiveField } from "@/lib/form-runtime/hooks";
import { cn } from "@/lib/utils";

import { FieldRenderer } from "./FieldRenderer";
import { useFormRuntime } from "./FormRuntimeContext";

import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface EditableFieldProps {
  field: FieldSchema;
  className?: string;
  /** When true, focus the input on mount (detail pane opens → focus first field). */
  autoFocus?: boolean;
}

/**
 * Single-field wrapper. Reads/writes through FormRuntimeContext, keeps
 * the URL's ``?field=`` in sync with the currently-focused input, and
 * renders the input itself via FieldRenderer.
 *
 * The URL is the single source of truth for "which field is active":
 * focusing an input updates the URL (via useActiveField), which in turn
 * re-renders FieldList + FieldDetail + FieldContextPanel consistently.
 * No internal focus state lives in the FormRuntimeContext anymore.
 */
export function EditableField({ field, className, autoFocus }: EditableFieldProps) {
  const { values, setFieldValue } = useFormRuntime();
  const { activeFieldId, setActiveField } = useActiveField();
  const value = values[field.path];
  const isFocused = activeFieldId === field.id;

  return (
    <div
      className={cn(
        "space-y-1.5",
        isFocused && "rounded-md ring-2 ring-ring ring-offset-2",
        className,
      )}
      onFocusCapture={() => {
        if (activeFieldId !== field.id) setActiveField(field.id);
      }}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setActiveField(null);
        }
      }}
    >
      <Label htmlFor={field.id} className="text-sm">
        {field.label}
        {field.required && <span className="ml-1 text-destructive">*</span>}
      </Label>
      <FieldRenderer
        field={field}
        value={value}
        onChange={(next) => setFieldValue(field.path, next)}
        autoFocus={autoFocus}
      />
      {field.hint && <p className="text-xs text-muted-foreground">{field.hint}</p>}
    </div>
  );
}
