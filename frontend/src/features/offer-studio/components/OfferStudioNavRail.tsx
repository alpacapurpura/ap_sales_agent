"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { FinderColumn } from "@/components/form-runtime";
import { cn } from "@/lib/utils";

import { useSectionsForArchetype } from "../hooks/use-sections-for-archetype";
import { OFFER_SECTIONS, type OfferSectionMeta } from "../lib/section-catalog";

import type { Offer } from "../types";

/**
 * Column 1 of the offer-studio editor Finder layout — the list of sections
 * resolved by ``resolvePresetSections`` + the archetype catalog. Dimensions
 * mirror the brand-studio ``BrandStudioNavRail``:
 *
 *   - width 260px (--brand-col-sections)
 *   - row height ~36px, padding 9px 14px
 *   - chevron on the right of every row
 *   - active row gets a 2px brand-coloured rail on the left edge
 *
 * Data is purely URL-driven — active slug extracted from ``usePathname`` —
 * so no parent callback is required. The legacy scroll-based
 * ``components/navigation/OfferNavRail.tsx`` (in-page anchor scrolling) is
 * kept until F4 retires the legacy editor shell; new app routes mount THIS
 * rail instead.
 *
 * Sections shown per offer depend on the offer's archetype (via
 * ``useSectionsForArchetype``) intersected with ``OFFER_SECTIONS``. The
 * catalog order is preserved so UX stays stable across archetype switches.
 */
export interface OfferStudioNavRailProps {
  offer: Offer;
  /**
   * Base path under which section slugs are appended to build hrefs —
   * defaults to ``/{tenantId}/offer-studio/offer/{offer.id}/editor``.
   * Consumers that mount the rail inside a non-editor tab can override.
   */
  baseHref?: string;
}

/**
 *
 */
export function OfferStudioNavRail({ offer, baseHref }: OfferStudioNavRailProps) {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();

  const resolvedBase =
    baseHref ?? (tenantId ? `/${tenantId}/offer-studio/offer/${offer.id}/editor` : "");

  const sectionsMeta = useSectionsForArchetype(offer.archetype);
  const resolvedKeys = useMemo(
    () => new Set(sectionsMeta?.map((s) => s.key) ?? []),
    [sectionsMeta],
  );
  const visibleSections = useMemo(
    () => OFFER_SECTIONS.filter((s) => resolvedKeys.size === 0 || resolvedKeys.has(s.slug)),
    [resolvedKeys],
  );

  const activeSlug = useMemo(
    () => extractActiveSectionSlug(pathname ?? "", offer.id),
    [pathname, offer.id],
  );

  return (
    <FinderColumn
      title="Secciones"
      count={visibleSections.length}
      widthClass="w-[var(--brand-col-sections)]"
      ariaLabel="Secciones de Offer Studio"
    >
      <ul className="flex flex-col">
        {visibleSections.map((section) => (
          <SectionRow
            key={section.slug}
            baseHref={resolvedBase}
            section={section}
            isActive={section.slug === activeSlug}
          />
        ))}
      </ul>
    </FinderColumn>
  );
}

interface SectionRowProps {
  baseHref: string;
  section: OfferSectionMeta;
  isActive: boolean;
}

function SectionRow({ baseHref, section, isActive }: SectionRowProps) {
  const Icon = section.icon;
  return (
    <li>
      <Link
        href={`${baseHref}/${section.slug}`}
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "relative flex items-center gap-2 border-b border-border/50",
          "px-[14px] py-[9px] text-[13px] transition-colors",
          isActive ? "bg-muted/60" : "hover:bg-muted/30",
          isActive &&
            "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
        )}
      >
        <Icon
          className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")}
          aria-hidden="true"
        />
        <span
          className={cn("flex-1 truncate", isActive ? "text-foreground" : "text-foreground/90")}
        >
          {section.label}
        </span>
        <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
      </Link>
    </li>
  );
}

/**
 * Extract the active section slug from an offer-studio pathname. Accepts
 * both the legacy URL
 * ``/.../offer/{id}/edition/{code}/{section}/{fieldId?}`` and the target
 * URL ``/.../offer/{id}/editor/{section}/{fieldId?}`` so the rail works
 * across the F3 migration without a rewrite.
 */
export function extractActiveSectionSlug(pathname: string, offerId: string): string | null {
  const marker = `/offer/${offerId}/`;
  const idx = pathname.indexOf(marker);
  if (idx < 0) return null;
  const rest = pathname
    .slice(idx + marker.length)
    .split("/")
    .filter(Boolean);
  if (rest.length === 0) return null;

  // Target URL: editor/{section}/...
  if (rest[0] === "editor" && rest[1]) return rest[1];
  // Legacy URL: edition/{code}/{section}/...
  if (rest[0] === "edition" && rest[2]) return rest[2];

  return null;
}
