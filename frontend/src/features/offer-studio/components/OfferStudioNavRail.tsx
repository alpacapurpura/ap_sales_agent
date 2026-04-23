"use client";

import { Check, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { FinderColumn } from "@/components/form-runtime";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useSectionStatus } from "@/features/copilot/hooks/use-section-status";
import { cn } from "@/lib/utils";

import { useOffer } from "../hooks/use-offer";
import { useSectionsForArchetype } from "../hooks/use-sections-for-archetype";
import { OFFER_SECTIONS, type OfferSectionMeta } from "../lib/section-catalog";

import type { SectionStatusEntry } from "@/features/copilot/hooks/use-section-status";

/**
 * Column 1 of the offer-studio editor Finder layout — the list of sections
 * resolved by ``resolvePresetSections`` + the archetype catalog. Mirrors
 * ``features/brand-studio/components/BrandStudioNavRail.tsx`` so both
 * studios share the same primitive:
 *
 *   - width 260px (--brand-col-sections)
 *   - row height ~36px, padding 9px 14px
 *   - chevron on the right of every row
 *   - active row gets a 2px brand-coloured rail on the left edge
 *
 * Self-contained: reads ``tenantId`` + ``id`` from URL params and fetches
 * the offer via ``useOffer`` (React Query de-dupes with the parent shell
 * query). No prop drilling — callers just mount ``<OfferStudioNavRail />``.
 *
 * Sections shown per offer depend on the offer's archetype (via
 * ``useSectionsForArchetype``) intersected with ``OFFER_SECTIONS``. The
 * catalog order is preserved so UX stays stable across archetype switches.
 * While the offer is loading the full catalog renders so the rail is never
 * blank during the first paint.
 */
export function OfferStudioNavRail() {
  const params = useParams<{ tenantId?: string; id?: string }>();
  const tenantId = params?.tenantId ?? "";
  const offerId = params?.id ?? "";
  const pathname = usePathname();

  const { offer } = useOffer(offerId);

  const resolvedBase =
    tenantId && offerId ? `/${tenantId}/offer-studio/offer/${offerId}/editor` : "";

  const sectionsMeta = useSectionsForArchetype(offer?.archetype);
  const resolvedKeys = useMemo(
    () => new Set(sectionsMeta?.map((s) => s.key) ?? []),
    [sectionsMeta],
  );
  const visibleSections = useMemo(
    () => OFFER_SECTIONS.filter((s) => resolvedKeys.size === 0 || resolvedKeys.has(s.slug)),
    [resolvedKeys],
  );

  const activeSlug = useMemo(
    () => (offerId ? extractActiveSectionSlug(pathname ?? "", offerId) : null),
    [pathname, offerId],
  );

  const sectionStatus = useSectionStatus("offer");

  return (
    <TooltipProvider>
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
              statusEntry={sectionStatus[section.slug]}
            />
          ))}
        </ul>
      </FinderColumn>
    </TooltipProvider>
  );
}

interface SectionRowProps {
  baseHref: string;
  section: OfferSectionMeta;
  isActive: boolean;
  statusEntry?: SectionStatusEntry;
}

function SectionRow({ baseHref, section, isActive, statusEntry }: SectionRowProps) {
  const Icon = section.icon;
  const status = statusEntry?.status ?? "idle";

  const linkContent = (
    <Link
      href={`${baseHref}/${section.slug}`}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "relative flex min-h-[36px] items-center gap-2 border-b border-border/50",
        "px-[14px] py-[9px] text-[13px] transition-colors",
        isActive ? "bg-muted/60" : "hover:bg-muted/30",
        isActive && "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
      )}
    >
      <Icon
        className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")}
        aria-hidden="true"
      />
      <span className={cn("flex-1 truncate", isActive ? "text-foreground" : "text-foreground/90")}>
        {section.label}
      </span>
      <SectionBadge statusEntry={statusEntry} />
      <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
    </Link>
  );

  if ((status === "running" || status === "completed") && statusEntry?.fieldIds?.length) {
    const tooltipText = statusEntry.fieldIds.join(", ");
    return (
      <li>
        <Tooltip>
          <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
          <TooltipContent side="right" className="max-w-[200px] text-xs">
            {tooltipText}
          </TooltipContent>
        </Tooltip>
      </li>
    );
  }

  return <li>{linkContent}</li>;
}

// ── Badge component ───────────────────────────────────────────────────────────

interface SectionBadgeProps {
  statusEntry?: SectionStatusEntry;
}

function SectionBadge({ statusEntry }: SectionBadgeProps) {
  const status = statusEntry?.status ?? "idle";
  const count = statusEntry?.fieldCount ?? 0;

  if (status === "idle") return null;

  if (status === "queued") {
    return (
      <span
        className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
        aria-label="En cola"
      >
        ·
      </span>
    );
  }

  if (status === "running") {
    return (
      <span className="flex shrink-0 items-center gap-1 rounded-full bg-brand/10 px-1.5 py-0.5 text-[10px] text-brand">
        <span
          className="h-2 w-2 rounded-full border-2 border-brand border-t-transparent animate-spin"
          aria-hidden="true"
        />
        {count > 0 ? `${count} entrando` : "…"}
      </span>
    );
  }

  // completed
  return (
    <span className="flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] text-success">
      <Check className="h-2.5 w-2.5" aria-hidden="true" />
      {`${count} sugeridos`}
    </span>
  );
}

/**
 * Extract the active section slug from an offer-studio pathname. Accepts
 * both the legacy URL ``/.../offer/{id}/edition/{code}/{section}`` and
 * the target URL ``/.../offer/{id}/editor/{section}`` so the rail works
 * across the F3 migration without a rewrite. Field selection lives in
 * ``?field=`` (query string) and is irrelevant for rail highlighting.
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
