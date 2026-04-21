import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

const MAX_LENGTH = 60;

/**
 * Extracts a human-readable summary string from an array item.
 *
 * Iterates fields in order, looking for the first text/textarea field
 * that has a non-empty value. Returns the value trimmed and truncated
 * to 60 characters. Returns "" when no text content is found.
 */
export function summariseItem(item: Row, fields: FieldSchema[]): string {
  for (const field of fields) {
    if (field.type !== "text" && field.type !== "textarea") continue;
    const val = item[field.path];
    if (typeof val !== "string") continue;
    const trimmed = val.trim();
    if (!trimmed) continue;
    return trimmed.slice(0, MAX_LENGTH);
  }
  return "";
}
