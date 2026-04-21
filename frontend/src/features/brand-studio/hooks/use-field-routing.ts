"use client";

import { useParams } from "next/navigation";

import { useActiveField } from "@/lib/form-runtime/hooks";

export interface FieldRouting {
  tenantId: string;
  section: string;
  /** Current active field id from the URL, or null for section-level view. */
  activeFieldId: string | null;
  /** Build the href to open a specific field (or back to section level when null). */
  getFieldHref: (fieldId: string | null) => string;
}

/**
 * Deep-linkable route contract for form-runtime sections.
 *
 *   /{tenantId}/brand-studio/{section}                → list view
 *   /{tenantId}/brand-studio/{section}?field={fieldId} → detail view
 *
 * Field selection is a client-side URL update (``?field=``) so it does
 * not trigger a server navigation — see ``useActiveField``. Section
 * changes remain pathname transitions (full Next.js navigation).
 */
export function useBrandStudioFieldRouting(section: string): FieldRouting {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const { activeFieldId, getFieldHref } = useActiveField();
  return { tenantId, section, activeFieldId, getFieldHref };
}
