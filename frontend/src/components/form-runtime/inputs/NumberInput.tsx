"use client";

import { Input } from "@/components/ui/input";

import type { BaseInputProps } from "./types";

/**
 *
 */
export function NumberInput({
  field,
  value,
  onChange,
  disabled,
  autoFocus,
  onBlur,
}: BaseInputProps<number | null>) {
  return (
    <Input
      id={field.id}
      type="number"
      value={value ?? ""}
      onChange={(e) => {
        const raw = e.target.value;
        onChange(raw === "" ? null : Number(raw));
      }}
      onBlur={onBlur}
      placeholder={field.placeholder}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
