"use client";

import { useParams } from "next/navigation";
import { useCallback } from "react";

import { useActiveField } from "@/lib/form-runtime/hooks";

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
 *   /{tenantId}/offer-studio/offer/{offerId}/editor/{section}
 *       → list view (activeFieldId = null)
 *
 *   /{tenantId}/offer-studio/offer/{offerId}/editor/{section}?field={fieldId}
 *       → detail view
 *
 * Field selection lives in the ``?field=`` query param and is mutated
 * client-side via ``useActiveField`` — pathname changes are reserved
 * for section transitions (full server navigation).
 *
 * The legacy edition-code segment has been replaced by the flat editor
 * route. ``editionCode`` is still exposed for consumers that have not
 * migrated yet; it defaults to ``"evergreen"`` when the route params do
 * not carry a ``code``.
 */
export function useOfferStudioFieldRouting(sectionOverride?: string): OfferFieldRouting {
  const params = useParams<{
    tenantId?: string;
    id?: string;
    code?: string;
    section?: string;
  }>();
  const tenantId = params?.tenantId ?? "";
  const offerId = params?.id ?? "";
  const editionCode = params?.code ?? "evergreen";
  const section = sectionOverride ?? params?.section ?? "";

  const { activeFieldId, getFieldHref } = useActiveField();

  const getSectionHref = useCallback(
    (sectionSlug: string) => `/${tenantId}/offer-studio/offer/${offerId}/editor/${sectionSlug}`,
    [tenantId, offerId],
  );

  return {
    tenantId,
    offerId,
    editionCode,
    section,
    activeFieldId,
    getFieldHref,
    getSectionHref,
  };
}
