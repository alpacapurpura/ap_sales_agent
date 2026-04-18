"use client";

import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

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
 *   /{tenantId}/brand-studio/{section}            → list view (activeFieldId = null)
 *   /{tenantId}/brand-studio/{section}/{fieldId}  → detail view
 *
 * Pages that render a `UniversalEditableSection` call this hook to derive the
 * `activeFieldId` + `getFieldHref` props from the URL. Consumers MUST invoke
 * it under a route whose params include `tenantId`, and the route file is
 * responsible for exposing the optional `[fieldId]` catch-all via
 * `[[...fieldId]]/page.tsx` or `[[fieldId]]/page.tsx`.
 */
export function useBrandStudioFieldRouting(section: string): FieldRouting {
  const params = useParams<{ tenantId?: string; fieldId?: string | string[] }>();
  const tenantId = params?.tenantId ?? "";

  const activeFieldId = useMemo(() => {
    const raw = params?.fieldId;
    if (!raw) return null;
    return Array.isArray(raw) ? (raw[0] ?? null) : raw;
  }, [params]);

  const getFieldHref = useCallback(
    (fieldId: string | null) => {
      const base = `/${tenantId}/brand-studio/${section}`;
      return fieldId === null ? base : `${base}/${fieldId}`;
    },
    [tenantId, section],
  );

  return { tenantId, section, activeFieldId, getFieldHref };
}
