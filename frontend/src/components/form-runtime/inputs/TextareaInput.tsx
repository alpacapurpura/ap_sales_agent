"use client";

import { InlineEditableTextarea } from "@/components/ui/inline-editable";

import type { BaseInputProps } from "./types";

/**
 * Converts a string[] from the backend to a newline-separated string for display.
 * Returns "" when the value is null, undefined, or empty — so the placeholder shows.
 */
function joinLines(value: unknown): string {
  if (Array.isArray(value)) {
    return (value as string[])
      .filter((v): v is string => typeof v === "string" && v.length > 0)
      .join("\n");
  }
  return typeof value === "string" ? value : "";
}

/**
 * Splits a newline-separated string into a string[].
 * Strips common bullet prefixes (•, ·, -, *) and trims whitespace.
 * Empty lines are discarded.
 */
function splitLines(raw: string): string[] {
  return raw
    .split("\n")
    .map((line) => line.replace(/^[\s•·\-*]+/, "").trim())
    .filter((line) => line.length > 0);
}

/**
 * Multi-line text field rendered as an InlineEditable textarea with
 * auto-resize (`react-textarea-autosize`). The textarea grows with the
 * content so long fields (historia, origen, dolor) read entirely without
 * internal scrollbars.
 *
 * When `field.storeAs === "newline_array"`, the component transparently
 * converts between the UI string (newline-separated) and the backend
 * string[] — split/join on-the-fly.  Autosave on-change is preserved.
 * Backward compatible: when storeAs is absent, behaviour is unchanged.
 */
export function TextareaInput({
  field,
  value,
  onChange,
  disabled,
  autoFocus,
  onBlur,
}: BaseInputProps<string | string[] | null>) {
  const isArrayMode = field.storeAs === "newline_array";

  const displayValue: string = isArrayMode ? joinLines(value) : ((value as string | null) ?? "");

  function handleChange(next: string): void {
    if (isArrayMode) {
      (onChange as (v: string[]) => void)(splitLines(next));
    } else {
      (onChange as (v: string) => void)(next);
    }
  }

  return (
    <InlineEditableTextarea
      id={field.id}
      value={displayValue}
      onChange={handleChange}
      onBlur={onBlur}
      placeholder={field.placeholder}
      minRows={field.rows ?? 2}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
