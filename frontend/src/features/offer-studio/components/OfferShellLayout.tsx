"use client";

/**
 * OfferShellLayout — offer-level shell (post-F4 canonical).
 *
 * Layout:
 *   ┌ Topbar (breadcrumb) ───────────────────────────────────────────┐
 *   ├ OfferShellHeader (title + status + actions) ──────────────────┤
 *   ├──────────────┬─────────────────────────────────────────────────┤
 *   │ VariantRail  │ TabBar + content (children)                     │
 *   │ (optional)   │                                                  │
 *   └──────────────┴─────────────────────────────────────────────────┘
 *
 * - Renders VariantRail only when `useShouldShowVariantRail` returns true.
 * - When shouldShow is false, the right pane fills the full width (pass-
 *   through layout) and the "Editions" tab is hidden.
 * - No React context provider — children read React Query directly via
 *   `useOffer`, `useParams`, or hook-level helpers.
 *
 * Exported helpers (also used by route files):
 *   - matchLegacyEditionPath  — parse the old /edition/{code}/{section} URL
 *   - buildLegacyEditionRedirectUrl — build the 301 target URL
 */

import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useEditions } from "../hooks/use-editions";
import { useOffer } from "../hooks/use-offer";
import { useOfferCounts } from "../hooks/use-offer-counts";
import { useRailCollapsed } from "../hooks/use-rail-collapsed";
import { useShouldShowVariantRail } from "../hooks/use-should-show-variant-rail";

import { OfferStudioTabBar } from "./OfferStudioTabBar";
import { EditionFormDialog } from "./editions/EditionFormDialog";
import { OfferShellHeader } from "./OfferShellHeader";
import { OfferStudioBreadcrumb } from "./OfferStudioBreadcrumb";
import { VariantRail } from "./variant-rail/VariantRail";

import type { LaunchEdition, LaunchEditionCreate, LaunchEditionUpdate } from "../types";

// ── Legacy edition redirect helpers ──────────────────────────────────────────

export interface LegacyEditionMatch {
  tenantId: string;
  offerId: string;
  code: string;
  section: string;
  fieldId: string | undefined;
}

/**
 * Parse a legacy `/offer/{id}/edition/{code}/{section}/{fieldId?}` pathname.
 * Returns null when the path does not match the legacy pattern.
 */
export function matchLegacyEditionPath(pathname: string): LegacyEditionMatch | null {
  const re =
    /^\/([^/]+)\/offer-studio\/offer\/([^/]+)\/edition\/([^/]+)\/([^/]+)(?:\/([^/?#]+))?(?:[/?#].*)?$/;
  const match = re.exec(pathname);
  if (!match) return null;
  return {
    tenantId: match[1],
    offerId: match[2],
    code: match[3],
    section: match[4],
    fieldId: match[5] ?? undefined,
  };
}

/**
 * Build the 301 redirect target URL from a parsed legacy edition match.
 */
export function buildLegacyEditionRedirectUrl(match: LegacyEditionMatch): string {
  const { tenantId, offerId, code, section, fieldId } = match;
  const base = `/${tenantId}/offer-studio/offer/${offerId}/editor/${section}`;
  const path = fieldId ? `${base}/${fieldId}` : base;
  return `${path}?edition=${code}`;
}

// ── OfferShellLayout component ────────────────────────────────────────────────

export interface OfferShellLayoutProps {
  offerId: string;
  tenantId: string;
  children: React.ReactNode;
}

/**
 *
 */
export function OfferShellLayout({ offerId, tenantId, children }: OfferShellLayoutProps) {
  const { offer, loading: offerLoading, error: offerError } = useOffer(offerId);
  const { data: counts, isLoading: countsLoading, error: countsError } = useOfferCounts(offerId);
  const { editions } = useEditions(offerId);
  const [railCollapsed, toggleRailCollapsed] = useRailCollapsed();

  const [editionFormOpen, setEditionFormOpen] = useState(false);
  const [editionFormSource, setEditionFormSource] = useState<LaunchEdition | undefined>(undefined);

  const { shouldShow: showVariantRail } = useShouldShowVariantRail({
    archetype: offer?.archetype,
    variants: editions,
  });

  const safeCounts = counts ?? {
    assets: 0,
    campaigns: 0,
    knowledge: 0,
    active_campaigns: 0,
  };

  if (offerLoading || countsLoading) {
    return (
      <div
        className="flex h-screen items-center justify-center bg-background"
        aria-label="Cargando oferta"
      >
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      </div>
    );
  }

  if (offerError || !offer) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background">
        <p className="font-medium text-destructive">{offerError ?? "Oferta no encontrada"}</p>
        <Link href={`/${tenantId}/offer-studio`}>
          <Button variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al Studio
          </Button>
        </Link>
      </div>
    );
  }

  if (countsError) {
    console.warn("No se pudieron cargar los conteos de la oferta", countsError);
  }

  const openNewEdition = () => {
    setEditionFormSource(undefined);
    setEditionFormOpen(true);
  };

  const handleEditionSave = async (data: LaunchEditionCreate | LaunchEditionUpdate) => {
    void data;
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <header
        className="flex h-[var(--brand-topbar-h,48px)] shrink-0 items-center gap-3 border-b border-border bg-background px-5"
        aria-label="Ruta de Offer Studio"
      >
        <OfferStudioBreadcrumb offerName={offer.name} />
      </header>

      <OfferShellHeader offer={offer} tenantId={tenantId} />

      <div className="flex min-h-0 flex-1">
        {showVariantRail && !railCollapsed ? (
          <VariantRail
            offerId={offerId}
            tenantId={tenantId}
            variants={editions}
            currentVariantId={null}
            onCollapse={toggleRailCollapsed}
            onCreateNew={openNewEdition}
          />
        ) : null}

        <div className="flex min-w-0 min-h-0 flex-1 flex-col">
          <OfferStudioTabBar
            tenantId={tenantId}
            offerId={offerId}
            counts={safeCounts}
            currentEditionId={null}
          />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>

      <EditionFormDialog
        open={editionFormOpen}
        onOpenChange={setEditionFormOpen}
        edition={editionFormSource}
        offerPricing={offer.pricing}
        currency={offer.currency ?? "USD"}
        onSave={handleEditionSave}
      />
    </div>
  );
}
