/**
 * Grid-column layout inference for multi-field editor grids.
 * Explicit ``field.layout`` always wins; otherwise we fall back on the field
 * type: wide fields (textarea/array/custom) occupy the full row, everything
 * else fits in one grid column.
 */

import type { FieldLayout, FieldSchema, FieldType } from "./types";

const DEFAULT_LAYOUT_BY_TYPE: Record<FieldType, FieldLayout> = {
  text: "half",
  url: "half",
  email: "half",
  number: "half",
  boolean: "half",
  enum: "half",
  textarea: "full",
  array: "full",
  custom: "full",
};

/** Resolve the effective layout for a single field. */
export function inferFieldLayout(field: FieldSchema): FieldLayout {
  return field.layout ?? DEFAULT_LAYOUT_BY_TYPE[field.type];
}

/**
 * Map a layout hint to the Tailwind grid-column-span utility used in the
 * editor grid. ``full`` spans the whole row on every breakpoint;
 * ``two-thirds`` spans 2 cols only on ≥3-col viewports (fallback to full).
 */
export function layoutToColSpanClass(layout: FieldLayout): string {
  switch (layout) {
    case "full":
      return "col-span-full";
    case "half":
      return "col-span-1";
    case "two-thirds":
      return "col-span-full xl:col-span-2";
  }
}
