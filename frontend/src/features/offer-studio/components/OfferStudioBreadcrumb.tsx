"use client";

import { ChevronRight } from "lucide-react";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { getOfferSectionLabel } from "../lib/section-catalog";

interface Crumb {
  label: string;
  /** Absolute href for navigation, undefined on the active leaf. */
  href?: string;
}

/**
 * Dynamic breadcrumb driven by the URL:
 *
 *   Offer Studio › {offer-name} › {section} › [{field}]
 *
 * The active leaf is rendered without a link so the user cannot navigate
 * to themselves. Mirrors ``features/brand-studio/components/
 * BrandStudioBreadcrumb.tsx`` — same ``buildCrumbs`` extraction + same
 * render shape — so both studios share visual parity.
 *
 * Path patterns understood (legacy + target):
 *
 *   /{t}/offer-studio                                                 → "Offer Studio"
 *   /{t}/offer-studio/offer/{id}                                       → + offer
 *   /{t}/offer-studio/offer/{id}/editor                                → + "Editor"
 *   /{t}/offer-studio/offer/{id}/editor/{section}                      → + section
 *   /{t}/offer-studio/offer/{id}/editor/{section}/{fieldId}            → + field
 *   /{t}/offer-studio/offer/{id}/edition/{code}/{section}              → legacy section
 *   /{t}/offer-studio/offer/{id}/edition/{code}/{section}/{fieldId}    → legacy field
 *   /{t}/offer-studio/offer/{id}/editions                              → + "Editions"
 *   /{t}/offer-studio/offer/{id}/editions/{editionId}                  → + edition name
 *   /{t}/offer-studio/offer/{id}/assets                                → + tab name
 */
export interface OfferStudioBreadcrumbProps {
  /**
   * Optional display name for the current offer. Shown between the root
   * and the first sub-tab. When absent the breadcrumb renders the
   * shortened id fallback so the crumb list stays non-empty.
   */
  offerName?: string;
}

/**
 *
 */
export function OfferStudioBreadcrumb({ offerName }: OfferStudioBreadcrumbProps = {}) {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();

  const crumbs = useMemo<Crumb[]>(
    () => buildCrumbs(pathname ?? "", tenantId, offerName),
    [pathname, tenantId, offerName],
  );

  return (
    <nav aria-label="Ruta" className="flex items-center gap-2 text-[13px]">
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-2">
            {index > 0 && (
              <ChevronRight className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
            )}
            {crumb.href && !isLast ? (
              <a
                href={crumb.href}
                className="text-muted-foreground transition-colors hover:text-foreground"
              >
                {crumb.label}
              </a>
            ) : (
              <span
                className={cn(isLast ? "font-medium text-foreground" : "text-muted-foreground")}
                aria-current={isLast ? "page" : undefined}
              >
                {crumb.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

const TOP_LEVEL_TAB_LABELS: Record<string, string> = {
  editor: "Editor",
  editions: "Editions",
  assets: "Assets",
  knowledge: "Conocimiento",
  campaigns: "Campañas",
  ventas: "Ventas",
};

function shortenId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id;
}

/** Build breadcrumb list from a pathname + tenant id. Exported for tests. */
export function buildCrumbs(pathname: string, tenantId: string, offerName?: string): Crumb[] {
  const root: Crumb = {
    label: "Offer Studio",
    href: tenantId ? `/${tenantId}/offer-studio` : undefined,
  };
  if (!pathname || !tenantId) return [root];

  const rest = extractOfferStudioRest(pathname);
  if (!rest || rest[0] !== "offer" || !rest[1]) return [root];

  const offerId = rest[1];
  const offerHref = `/${tenantId}/offer-studio/offer/${offerId}`;
  const offerCrumb: Crumb = {
    label: offerName ?? `Oferta ${shortenId(offerId)}`,
    href: offerHref,
  };
  const crumbs: Crumb[] = [root, offerCrumb];

  const tabSegment = rest[2];
  if (!tabSegment) return crumbs;

  if (tabSegment === "edition") {
    appendLegacyEditionCrumbs(crumbs, offerHref, rest);
    return crumbs;
  }

  appendTabCrumb(crumbs, tabSegment, offerHref);
  appendTabBodyCrumbs(crumbs, tabSegment, rest.slice(3));
  return crumbs;
}

/** Return the pathname segments after "offer-studio" or null if absent. */
function extractOfferStudioRest(pathname: string): string[] | null {
  const parts = pathname.split("/").filter(Boolean);
  const idx = parts.indexOf("offer-studio");
  if (idx < 0) return null;
  const rest = parts.slice(idx + 1);
  return rest.length === 0 ? null : rest;
}

/**
 * Legacy URL flatten: ``/offer/{id}/edition/{code}/{section?}/{fieldId?}``
 * always collapses to Editor + section + field — editions never got their
 * own tab breadcrumb under the old routing.
 */
function appendLegacyEditionCrumbs(crumbs: Crumb[], offerHref: string, rest: string[]): void {
  crumbs.push({ label: "Editor", href: `${offerHref}/editor` });
  const section = rest[4];
  const fieldId = rest[5];
  if (!section) return;
  crumbs.push({ label: getOfferSectionLabel(section), href: undefined });
  if (fieldId) crumbs.push({ label: fieldId });
}

/** Push the top-level tab crumb, falling back to the raw segment for unknowns. */
function appendTabCrumb(crumbs: Crumb[], tabSegment: string, offerHref: string): void {
  const tabLabel = TOP_LEVEL_TAB_LABELS[tabSegment] ?? tabSegment;
  crumbs.push({ label: tabLabel, href: `${offerHref}/${tabSegment}` });
}

/** Append tab-specific sub-crumbs (section + field for editor, edition id for editions). */
function appendTabBodyCrumbs(crumbs: Crumb[], tabSegment: string, tail: string[]): void {
  if (tabSegment === "editor") {
    const [section, fieldId] = tail;
    if (section) crumbs.push({ label: getOfferSectionLabel(section), href: undefined });
    if (fieldId) crumbs.push({ label: fieldId });
    return;
  }
  if (tabSegment === "editions" && tail[0]) {
    crumbs.push({ label: `Edición ${shortenId(tail[0])}` });
  }
}
