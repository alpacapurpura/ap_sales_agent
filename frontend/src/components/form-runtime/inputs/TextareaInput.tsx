"use client";

import { InlineEditableTextarea } from "@/components/ui/inline-editable";

import type { BaseInputProps } from "./types";

/**
 * Multi-line text field rendered as an InlineEditable textarea with
 * auto-resize (`react-textarea-autosize`). The textarea grows with the
 * content so long fields (historia, origen, dolor) read entirely without
 * internal scrollbars.
 */
export function TextareaInput({
  field,
  value,
  onChange,
  disabled,
  autoFocus,
  onBlur,
}: BaseInputProps<string>) {
  return (
    <InlineEditableTextarea
      id={field.id}
      value={value ?? ""}
      onChange={onChange}
      onBlur={onBlur}
      placeholder={field.placeholder}
      minRows={field.rows ?? 2}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
