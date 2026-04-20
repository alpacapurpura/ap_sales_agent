import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface BaseInputProps<TValue = unknown> {
  field: FieldSchema;
  value: TValue;
  onChange: (next: TValue) => void;
  disabled?: boolean;
  autoFocus?: boolean;
  onBlur?: () => void;
}
