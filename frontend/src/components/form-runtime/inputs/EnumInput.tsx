"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type { BaseInputProps } from "./types";

/**
 *
 */
export function EnumInput({ field, value, onChange, disabled }: BaseInputProps<string>) {
  return (
    <Select value={value ?? ""} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger id={field.id} aria-required={field.required}>
        <SelectValue placeholder={field.placeholder ?? "Seleccionar..."} />
      </SelectTrigger>
      <SelectContent>
        {(field.options ?? []).map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
