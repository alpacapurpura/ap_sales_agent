import { NextResponse, type NextRequest } from "next/server";

/**
 * Edge middleware — legacy URL redirects.
 *
 * Phase 2 of the form-runtime URL refactor collapsed the per-field path
 * segment (``/editor/{section}/{fieldId}``) into a query parameter
 * (``/editor/{section}?field={fieldId}``). Bookmarks, copilot payloads
 * emitted before the cutover, and any hand-written deep links that used
 * the path-segment shape would otherwise 404 after the catch-all routes
 * were removed.
 *
 * This middleware rewrites every known legacy shape to its modern
 * equivalent with HTTP 308 (permanent, preserves method + body) so
 * external tools pick up the canonical URL in their caches.
 *
 * Patterns handled (tenantId is the first segment for every pattern):
 *
 *   /{t}/offer-studio/offer/{o}/editor/{section}/{fieldId}
 *   /{t}/offer-studio/offer/{o}/editor/(testimonials|faq|instructors)/{instanceId}/{fieldId}
 *   /{t}/offer-studio/offer/{o}/edition/{code}/{section}/{fieldId}
 *   /{t}/brand-studio/{section}/{fieldId}                        (section NOT collection root)
 *   /{t}/brand-studio/(team|authority|testimonials)/instance/{id}/{fieldId}
 *   /{t}/brand-studio/publico/persona/{personaId}/{fieldId}
 *
 * The middleware intentionally runs only for paths that start with
 * ``/{t}/offer-studio`` or ``/{t}/brand-studio`` — see ``matcher`` below.
 */

/** Brand-studio slugs that own their own sub-tree and therefore are NOT followed by a fieldId. */
const BRAND_COLLECTION_ROOTS = new Set(["team", "authority", "testimonials", "publico"]);

/** Offer-studio collection slugs that expose an instance detail route. */
const OFFER_COLLECTION_SLUGS = new Set(["testimonials", "faq", "instructors"]);

interface RedirectMatch {
  pathname: string;
  field: string;
  /** Additional query params to preserve in the redirect (e.g. edition code). */
  extraParams?: Record<string, string>;
}

function matchOfferEditorField(pathname: string): RedirectMatch | null {
  // /{t}/offer-studio/offer/{o}/editor/{section}/{fieldId}
  const re = /^\/([^/]+)\/offer-studio\/offer\/([^/]+)\/editor\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, offerId, section, fieldOrInstance] = m;
  // Collections have their own instance detail route — skip here and let
  // matchOfferEditorCollectionField handle the 5-segment variant.
  if (OFFER_COLLECTION_SLUGS.has(section)) return null;
  return {
    pathname: `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}`,
    field: fieldOrInstance,
  };
}

function matchOfferEditorCollectionField(pathname: string): RedirectMatch | null {
  // /{t}/offer-studio/offer/{o}/editor/(testimonials|faq|instructors)/{instanceId}/{fieldId}
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

function matchOfferLegacyEditionField(pathname: string): RedirectMatch | null {
  // /{t}/offer-studio/offer/{o}/edition/{code}/{section}/{fieldId}
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

function matchBrandSectionField(pathname: string): RedirectMatch | null {
  // /{t}/brand-studio/{section}/{fieldId}  (section must NOT be a collection root)
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

function matchBrandCollectionInstanceField(pathname: string): RedirectMatch | null {
  // /{t}/brand-studio/(team|authority|testimonials)/instance/{id}/{fieldId}
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

function matchBrandPersonaField(pathname: string): RedirectMatch | null {
  // /{t}/brand-studio/publico/persona/{personaId}/{fieldId}
  const re = /^\/([^/]+)\/brand-studio\/publico\/persona\/([^/]+)\/([^/]+)\/?$/;
  const m = re.exec(pathname);
  if (!m) return null;
  const [, tenantId, personaId, fieldId] = m;
  return {
    pathname: `/${tenantId}/brand-studio/publico/persona/${personaId}`,
    field: fieldId,
  };
}

const MATCHERS: Array<(p: string) => RedirectMatch | null> = [
  matchOfferEditorCollectionField, // 5-segment variants first
  matchOfferLegacyEditionField,
  matchBrandCollectionInstanceField,
  matchBrandPersonaField,
  matchOfferEditorField,
  matchBrandSectionField,
];

/**
 *
 */
export function middleware(request: NextRequest): NextResponse {
  const { pathname, searchParams } = request.nextUrl;

  for (const match of MATCHERS) {
    const hit = match(pathname);
    if (!hit) continue;

    const url = request.nextUrl.clone();
    url.pathname = hit.pathname;
    // Preserve any existing search params, then layer extra + field.
    for (const [k, v] of searchParams.entries()) {
      url.searchParams.set(k, v);
    }
    if (hit.extraParams) {
      for (const [k, v] of Object.entries(hit.extraParams)) {
        url.searchParams.set(k, v);
      }
    }
    url.searchParams.set("field", hit.field);
    return NextResponse.redirect(url, 308);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:tenantId/offer-studio/:path*", "/:tenantId/brand-studio/:path*"],
};
