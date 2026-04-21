/**
 * Helpers for building URLs inside the Offer Studio's edition-aware tree.
 *
 * URL shape (see DECISIONS.md D-route):
 *   /offer/{offerId}                                   Info (always)
 *   /offer/{offerId}/ventas                            Offer-level tab (evergreen)
 *   /offer/{offerId}/assets
 *   /offer/{offerId}/campaigns
 *   /offer/{offerId}/landing
 *   /offer/{offerId}/editions/{editionId}              Edition default (redirects)
 *   /offer/{offerId}/editions/{editionId}/ventas       Per-edition tab
 *   /offer/{offerId}/editions/{editionId}/assets
 *   /offer/{offerId}/editions/{editionId}/campaigns
 *   /offer/{offerId}/editions/{editionId}/landing
 */

/** Known terminal tab segments inside an offer or an edition. */
export const OFFER_TAB_SEGMENTS = ["ventas", "assets", "campaigns", "landing"] as const;
export type OfferTabSegment = (typeof OFFER_TAB_SEGMENTS)[number];

/**
 * Parse the path relative to `base` (= `/{tenant}/offer-studio/offer/{offerId}`)
 * and return the tab segment the user is currently viewing, if any.
 *
 * Recognises both path shapes:
 *   `${base}/ventas`                           → "ventas"
 *   `${base}/editions/{eid}/ventas`            → "ventas"
 *   `${base}` (Info)                           → null
 *   `${base}/editions/{eid}` (edition default) → null
 *   anything else                              → null
 */
export function currentOfferTabSegment(
  pathname: string | null | undefined,
  base: string,
): OfferTabSegment | null {
  if (!pathname?.startsWith(base)) return null;
  const rest = pathname.slice(base.length);
  if (!rest) return null;

  // Either `/editions/{eid}/{maybe tab}` or `/{maybe tab}`.
  const editionMatch = /^\/editions\/[^/]+(\/([^/?#]+))?/.exec(rest);
  if (editionMatch) {
    const tab = editionMatch[2];
    return isTabSegment(tab) ? tab : null;
  }

  const directMatch = /^\/([^/?#]+)/.exec(rest);
  if (directMatch) {
    const tab = directMatch[1];
    return isTabSegment(tab) ? tab : null;
  }

  return null;
}

/**
 * Build the destination path when the user switches to `newEditionId`
 * from the current pathname, preserving whichever tab the user was on.
 */
export function buildEditionSwitchHref(
  pathname: string | null | undefined,
  base: string,
  newEditionId: string,
): string {
  const tab = currentOfferTabSegment(pathname, base);
  const editionRoot = `${base}/editions/${newEditionId}`;
  return tab ? `${editionRoot}/${tab}` : editionRoot;
}

function isTabSegment(value: string | undefined): value is OfferTabSegment {
  return !!value && (OFFER_TAB_SEGMENTS as readonly string[]).includes(value);
}
