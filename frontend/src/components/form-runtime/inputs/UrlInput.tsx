"use client";

import { Input } from "@/components/ui/input";

import type { BaseInputProps } from "./types";

/**
 *
 */
export function UrlInput({
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
      type="url"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      placeholder={field.placeholder ?? "https://..."}
      inputMode="url"
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
