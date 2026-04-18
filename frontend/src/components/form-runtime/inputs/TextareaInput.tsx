"use client";

import { Textarea } from "@/components/ui/textarea";

import type { BaseInputProps } from "./types";

/**
 *
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
    <Textarea
      id={field.id}
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      placeholder={field.placeholder}
      rows={field.rows ?? 3}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
