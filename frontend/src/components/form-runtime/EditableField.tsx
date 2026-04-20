"use client";

import { Label } from "@/components/ui/label";
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
 * Single-field wrapper. Reads/writes through FormRuntimeContext, manages
 * focus dispatching, renders via FieldRenderer. Replaces WithCopilot — the
 * copilot sees this field through the bridge, not a per-element attribute.
 */
export function EditableField({ field, className, autoFocus }: EditableFieldProps) {
  const { values, setFieldValue, focusField, focusedFieldId } = useFormRuntime();
  const value = values[field.path];
  const isFocused = focusedFieldId === field.id;

  return (
    <div
      className={cn(
        "space-y-1.5",
        isFocused && "rounded-md ring-2 ring-ring ring-offset-2",
        className,
      )}
      onFocusCapture={() => focusField(field.id)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          focusField(null);
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
