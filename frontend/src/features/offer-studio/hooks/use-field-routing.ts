"use client";

import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

export interface OfferFieldRouting {
  tenantId: string;
  offerId: string;
  editionCode: string;
  section: string;
  /** Current active field id from the URL, or null for section-level view. */
  activeFieldId: string | null;
  /** Build the href to open a specific field (or back to section level when null). */
  getFieldHref: (fieldId: string | null) => string;
  /** Build the href to swap to another section inside the same edition. */
  getSectionHref: (sectionSlug: string) => string;
}

/**
 * Deep-linkable route contract for offer-studio sections.
 *
 *   /{tenantId}/offer-studio/offer/{offerId}/edition/{editionCode}/{section}
 *       → list view (activeFieldId = null)
 *
 *   /{tenantId}/offer-studio/offer/{offerId}/edition/{editionCode}/{section}/{fieldId}
 *       → detail view
 *
 * Mirrors ``useBrandStudioFieldRouting`` so both studios keep the same
 * primitive. Offer-studio adds the ``offerId`` + ``editionCode`` segments
 * because a section lives inside a specific offer's specific edition — the
 * brand equivalent is implicit (tenant-scoped singletons).
 *
 * Consumers MUST invoke it under a route whose params include
 * ``tenantId``, ``id`` (the offer id), ``code`` (the edition code) and
 * ``section``. The optional ``[[...fieldId]]`` catch-all feeds the
 * ``activeFieldId``.
 */
export function useOfferStudioFieldRouting(sectionOverride?: string): OfferFieldRouting {
  const params = useParams<{
    tenantId?: string;
    id?: string;
    code?: string;
    section?: string;
    fieldId?: string | string[];
  }>();
  const tenantId = params?.tenantId ?? "";
  const offerId = params?.id ?? "";
  const editionCode = params?.code ?? "";
  const section = sectionOverride ?? params?.section ?? "";

  const activeFieldId = useMemo(() => {
    const raw = params?.fieldId;
    if (!raw) return null;
    return Array.isArray(raw) ? (raw[0] ?? null) : raw;
  }, [params]);

  const baseEditionPath = `/${tenantId}/offer-studio/offer/${offerId}/edition/${editionCode}`;

  const getFieldHref = useCallback(
    (fieldId: string | null) => {
      const base = `${baseEditionPath}/${section}`;
      return fieldId === null ? base : `${base}/${fieldId}`;
    },
    [baseEditionPath, section],
  );

  const getSectionHref = useCallback(
    (sectionSlug: string) => `${baseEditionPath}/${sectionSlug}`,
    [baseEditionPath],
  );

  return { tenantId, offerId, editionCode, section, activeFieldId, getFieldHref, getSectionHref };
}
