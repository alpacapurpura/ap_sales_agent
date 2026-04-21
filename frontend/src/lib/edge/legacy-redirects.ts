/**
 * Legacy URL redirect matchers for the form-runtime Phase 2 refactor.
 *
 * Phase 2 collapsed the per-field path segment
 * (``/editor/{section}/{fieldId}``) into a query parameter
 * (``/editor/{section}?field={fieldId}``). Bookmarks, copilot payloads
 * emitted before the cutover, and hand-written deep links would otherwise
 * 404 after the catch-all routes were removed. These matchers recognise
 * every known legacy shape so the edge layer can 308-redirect them to the
 * canonical URL.
 *
 * Pure functions — no Next.js or Node runtime dependencies — so the module
 * is edge-safe and unit-testable in isolation.
 *
 * Patterns handled (tenantId is always the first segment):
 *
 *   /{t}/offer-studio/offer/{o}/editor/{section}/{fieldId}
 *   /{t}/offer-studio/offer/{o}/editor/(testimonials|faq|instructors)/{instanceId}/{fieldId}
 *   /{t}/offer-studio/offer/{o}/edition/{code}/{section}/{fieldId}
 *   /{t}/brand-studio/{section}/{fieldId}                        (section NOT collection root)
 *   /{t}/brand-studio/(team|authority|testimonials)/instance/{id}/{fieldId}
 *   /{t}/brand-studio/publico/persona/{personaId}/{fieldId}
 */

export interface LegacyRedirect {
  pathname: string;
  field: string;
  /** Additional query params to preserve in the redirect (e.g. edition code). */
  extraParams?: Record<string, string>;
}

/** Brand-studio slugs that own their own sub-tree (NOT followed by a fieldId). */
const BRAND_COLLECTION_ROOTS = new Set(["team", "authority", "testimonials", "publico"]);

/** Offer-studio collection slugs that expose an instance detail route. */
const OFFER_COLLECTION_SLUGS = new Set(["testimonials", "faq", "instructors"]);

function matchOfferEditorField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/offer-studio\/offer\/([^/]+)\/editor\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, offerId, section, fieldOrInstance] = m;
  if (OFFER_COLLECTION_SLUGS.has(section)) return null;
  return {
    pathname: `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}`,
    field: fieldOrInstance,
  };
}

function matchOfferEditorCollectionField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/offer-studio\/offer\/([^/]+)\/editor\/([^/]+)\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, offerId, section, instanceId, fieldId] = m;
  if (!OFFER_COLLECTION_SLUGS.has(section)) return null;
  return {
    pathname: `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}/${instanceId}`,
    field: fieldId,
  };
}

function matchOfferLegacyEditionField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/offer-studio\/offer\/([^/]+)\/edition\/([^/]+)\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, offerId, code, section, fieldId] = m;
  return {
    pathname: `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}`,
    field: fieldId,
    extraParams: { edition: code },
  };
}

function matchBrandSectionField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/brand-studio\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, section, fieldId] = m;
  if (BRAND_COLLECTION_ROOTS.has(section)) return null;
  return {
    pathname: `/${tenantId}/brand-studio/${section}`,
    field: fieldId,
  };
}

function matchBrandCollectionInstanceField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/brand-studio\/([^/]+)\/instance\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, section, instanceId, fieldId] = m;
  if (!BRAND_COLLECTION_ROOTS.has(section)) return null;
  return {
    pathname: `/${tenantId}/brand-studio/${section}/instance/${instanceId}`,
    field: fieldId,
  };
}

function matchBrandPersonaField(pathname: string): LegacyRedirect | null {
  const re = /^\/([^/]+)\/brand-studio\/publico\/persona\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, personaId, fieldId] = m;
  return {
    pathname: `/${tenantId}/brand-studio/publico/persona/${personaId}`,
    field: fieldId,
  };
}

// Order matters: the longer (5-segment) variants must run before the
// 4-segment variants so they do not get shadowed by the shorter regex.
const MATCHERS: readonly ((p: string) => LegacyRedirect | null)[] = [
  matchOfferEditorCollectionField,
  matchOfferLegacyEditionField,
  matchBrandCollectionInstanceField,
  matchBrandPersonaField,
  matchOfferEditorField,
  matchBrandSectionField,
];

/**
 * Returns the canonical rewrite target for a legacy form-runtime URL, or
 * ``null`` when the pathname is already modern (or unrelated). Intended to be
 * consumed from the edge layer (``src/proxy.ts``) to emit a 308 redirect.
 */
export function matchLegacyFormRuntimeRedirect(pathname: string): LegacyRedirect | null {
  for (const match of MATCHERS) {
    const hit = match(pathname);
    if (hit) return hit;
  }
  return null;
}
