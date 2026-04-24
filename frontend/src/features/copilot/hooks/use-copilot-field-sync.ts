import { useEffect } from "react";

import type { UseFormSetValue } from "react-hook-form";

/** Duration of the visual pulse applied to a freshly-filled input. */
const SHIMMER_DURATION_MS = 3000;

/**
 * Apply the existing ``copilot-highlight`` animation class (see globals.css)
 * to the input element matching the given form field name. Idempotent — if
 * the element is already pulsing, the class is refreshed for a new cycle.
 *
 * Fails silently when the input is not in the DOM (e.g. user is on another
 * section): shimmer is purely observational, not a correctness mechanism.
 */
function shimmerInput(formField: string): void {
  if (typeof document === "undefined") return;
  const selector = `[name="${CSS.escape(formField)}"], [data-field="${CSS.escape(formField)}"]`;
  const el = document.querySelector<HTMLElement>(selector);
  if (!el) return;
  const target: HTMLElement = el.closest<HTMLElement>("[data-field-pulse-target]") ?? el;
  target.classList.remove("copilot-highlight");
  // Force a reflow so the animation restarts if applied back-to-back
  void target.offsetWidth;
  target.classList.add("copilot-highlight");
  window.setTimeout(() => {
    target.classList.remove("copilot-highlight");
  }, SHIMMER_DURATION_MS);
}

/**
 * Subscribes to ``copilot:field-update`` events and either updates the form
 * or pulses the input, depending on the event shape:
 *
 * - ``newValue`` is a real value → call ``setValue(formField, newValue)`` so
 *   React Hook Form reflects it (classic copilot patch flow).
 * - ``newValue`` is ``null``/``undefined`` → treat the event as an "arrived"
 *   signal only and NEVER call ``setValue`` — the form's React Query cache
 *   will be re-hydrated by ``useAsyncToolJob`` invalidating the relevant key.
 *   Calling ``setValue(field, null)`` in this mode would blank fields that
 *   the extraction service had just populated (silent data loss).
 *
 * In both cases we apply the ``copilot-highlight`` pulse to the input so
 * the user sees which field was just touched.
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
      const { detail } = e as CustomEvent<{ fieldId: string; newValue: unknown }>;
      const { fieldId, newValue } = detail;
      const formField = fieldMap?.[fieldId] ?? fieldId;

      // Only write the value when it is a real payload. Null/undefined is a
      // "field arrived, value lives on the server" signal from polling; the
      // form picks it up via React Query invalidation.
      if (newValue !== null && newValue !== undefined) {
        setValue(formField, newValue, {
          shouldDirty: true,
          shouldValidate: true,
        });
      }

      shimmerInput(formField);
    };
    window.addEventListener("copilot:field-update", handler);
    return () => window.removeEventListener("copilot:field-update", handler);
  }, [setValue, fieldMap]);
}
