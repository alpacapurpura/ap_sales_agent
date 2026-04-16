import { useEffect } from "react";

import type { UseFormSetValue } from "react-hook-form";

/**
 * Subscribes to copilot:field-update events and updates the form.
 *
 * @param setValue - React Hook Form setValue function
 * @param fieldMap - Maps copilot field_ids to form field names (if different)
 *                   e.g. { "uvp": "positioning.uvp", "brand_name": "identity.brand_name" }
 *                   If not provided, uses field_id directly as form field name.
 */
export function useCopilotFieldSync(
  setValue: UseFormSetValue<Record<string, unknown>>,
  fieldMap?: Record<string, string>,
) {
  useEffect(() => {
    const handler = (e: Event) => {
      const { fieldId, newValue } = (e as CustomEvent).detail;
      const formField = fieldMap?.[fieldId] ?? fieldId;
      setValue(formField, newValue, {
        shouldDirty: true,
        shouldValidate: true,
      });
    };
    window.addEventListener("copilot:field-update", handler);
    return () => window.removeEventListener("copilot:field-update", handler);
  }, [setValue, fieldMap]);
}
