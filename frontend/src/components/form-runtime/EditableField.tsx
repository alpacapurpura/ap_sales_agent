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
 * URL-ownership invariant:
 *
 *   ``?field=`` is a pull target — UI reads it to render the active
 *   field. Only explicit user selection gestures may push to it:
 *     1. Clicking a row in FieldList (``onSelect``).
 *     2. Focusing the input itself (``onFocusCapture`` below).
 *     3. Section navigation (path change, handled by Next.js router).
 *
 *   Blur is NOT a selection gesture — a blur can fire for any reason
 *   (click on background, click on sidebar, tab to browser chrome, a
 *   sibling widget stealing focus). Treating blur as "deselect" lets
 *   incidental DOM events silently rewrite semantic user state, and
 *   combined with ``UniversalEditableSection``'s
 *   ``activeFieldId ?? firstField.id`` visual fallback it manifests as
 *   the editor "snapping back to the first field" on every stray
 *   click. The wrapper therefore only handles focus, never blur.
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
