/**
 * Pure route resolver for offer-studio editor section pages.
 *
 * Route shape: /{tenantId}/offer-studio/offer/{offerId}/editor/{section}/[[...fieldId]]
 *
 * The catch-all may accumulate stale segments when users click successive
 * field rows — ``activeFieldId`` is always the first segment and
 * ``sectionBasePath`` always collapses back to the section root so the
 * next href replaces (not appends) the trailing field.
 */
export interface OfferEditorRouteInput {
  tenantId: string;
  offerId: string;
  section: string;
  fieldId?: string | string[];
}

export interface OfferEditorRouteResult {
  activeFieldId: string | null;
  sectionBasePath: string;
}

/** Resolve active field + section base path from offer-studio editor route params. */
export function resolveOfferEditorRoute({
  tenantId,
  offerId,
  section,
  fieldId,
}: OfferEditorRouteInput): OfferEditorRouteResult {
  const active = Array.isArray(fieldId) ? (fieldId[0] ?? null) : (fieldId ?? null);
  const sectionBasePath = `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}`;
  return { activeFieldId: active, sectionBasePath };
}
