import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

/**
 * Computes the validation status of a single array item against its field schemas.
 *
 * Returns:
 * - "complete"                    — all required fields are non-empty
 * - "required-<field-path>"       — first required field that is missing/empty
 *
 * Optional fields do not affect completeness. The check is purely against
 * required fields to keep the UX signal unambiguous.
 */
export function computeItemStatus(
  item: Row,
  fields: FieldSchema[],
): `complete` | `required-${string}` {
  for (const field of fields) {
    if (!field.required) continue;
    const val = item[field.path];
    const isEmpty = val === undefined || val === null || (typeof val === "string" && !val.trim());
    if (isEmpty) {
      return `required-${field.path}`;
    }
  }
  return "complete";
}
