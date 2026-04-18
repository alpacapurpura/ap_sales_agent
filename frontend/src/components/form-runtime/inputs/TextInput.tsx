"use client";

import { Input } from "@/components/ui/input";

import type { BaseInputProps } from "./types";

/**
 *
 */
export function TextInput({
  field,
  value,
  onChange,
  disabled,
  autoFocus,
  onBlur,
}: BaseInputProps<string>) {
  return (
    <Input
      id={field.id}
      type="text"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      placeholder={field.placeholder}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
