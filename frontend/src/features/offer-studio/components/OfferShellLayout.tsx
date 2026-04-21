"use client";

/**
 * OfferShellLayout — offer-level shell for the F3 app-route migration.
 *
 * Layout:
 *   ┌ Topbar (breadcrumb) ───────────────────────────────────────────┐
 *   ├ Row 1 (title + status + actions) ─────────────────────────────┤
 *   ├──────────────┬─────────────────────────────────────────────────┤
 *   │ VariantRail  │ TabBar + content (children)                     │
 *   │ (optional)   │                                                  │
 *   └──────────────┴─────────────────────────────────────────────────┘
 *
 * - Renders VariantRail only when `useShouldShowVariantRail` returns true.
 * - When shouldShow is false, the right pane fills the full width (pass-
 *   through layout) and the "Editions" tab is hidden.
 * - Uses the existing OfferShell context (OfferShellContext) that is
 *   provided by the legacy layout.tsx during the F3→F5 migration window.
 *   Post-F5 this component takes over as the sole provider.
 *
 * Exported helpers (also used by route files):
 *   - matchLegacyEditionPath  — parse the old /edition/{code}/{section} URL
 *   - buildLegacyEditionRedirectUrl — build the 301 target URL
 *
 * Architecture:
 *   Client Component — reads editions via useEditions, offer via useOffer.
 *   The shell is mounted once per offer by layout.tsx (App Router layout
 *   preserves the tree across page navigations within the offer).
 */

import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState, useMemo } from "react";

import { Button } from "@/components/ui/button";

import {
  OfferShellContext,
  OfferAutoSaveContext,
  DEFAULT_SNAPSHOT,
} from "../context/OfferShellContext";
import { useEditions } from "../hooks/use-editions";
import { useOffer } from "../hooks/use-offer";
import { useOfferCounts } from "../hooks/use-offer-counts";
import { useRailCollapsed } from "../hooks/use-rail-collapsed";
import { useShouldShowVariantRail } from "../hooks/use-should-show-variant-rail";

import { OfferShellHeaderRow1 } from "./container/OfferShellHeaderRow1";
import { OfferTabBar } from "./container/OfferTabBar";
import { EditionFormDialog } from "./editions/EditionFormDialog";
import { OfferStudioBreadcrumb } from "./OfferStudioBreadcrumb";
import { VariantRail } from "./variant-rail/VariantRail";

import type {
  OfferShellContextValue,
  OfferAutoSaveSnapshot,
  OfferAutoSaveContextValue,
} from "../context/OfferShellContext";
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
 *
 * Used by the 30-day redirect shim in the legacy catch-all route.
 */
export function matchLegacyEditionPath(pathname: string): LegacyEditionMatch | null {
  // Pattern: /{tenantId}/offer-studio/offer/{offerId}/edition/{code}/{section}[/{fieldId}]
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
 *
 * Old URL: /{t}/offer-studio/offer/{id}/edition/{code}/{section}/{fieldId?}
 * New URL: /{t}/offer-studio/offer/{id}/editor/{section}/{fieldId?}?edition={code}
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
 * Client Component shell wrapping all offer-studio routes under
 * `/offer/[id]/`. Replaces the legacy `OfferShell` during the F3 migration
 * window and is fully compatible with the existing `OfferShellContext`.
 */
export function OfferShellLayout({ offerId, tenantId, children }: OfferShellLayoutProps) {
  const { offer, loading: offerLoading, error: offerError } = useOffer(offerId);
  const { data: counts, isLoading: countsLoading, error: countsError } = useOfferCounts(offerId);
  const { editions } = useEditions(offerId);
  const [railCollapsed, toggleRailCollapsed] = useRailCollapsed();

  const [snapshot, setSnapshot] = useState<OfferAutoSaveSnapshot>(DEFAULT_SNAPSHOT);
  const [editionFormOpen, setEditionFormOpen] = useState(false);
  const [editionFormSource, setEditionFormSource] = useState<LaunchEdition | undefined>(undefined);

  const { shouldShow: showVariantRail } = useShouldShowVariantRail({
    archetype: offer?.archetype,
    variants: editions,
  });

  const safeCounts = useMemo(
    () =>
      counts ?? {
        assets: 0,
        campaigns: 0,
        knowledge: 0,
        active_campaigns: 0,
      },
    [counts],
  );

  const shellValue = useMemo<OfferShellContextValue | null>(() => {
    if (!offer) return null;
    return { offer, counts: safeCounts, tenantId };
  }, [offer, safeCounts, tenantId]);

  const autoSaveValue = useMemo<OfferAutoSaveContextValue>(
    () => ({ ...snapshot, setSnapshot }),
    [snapshot],
  );

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

  if (offerError || !offer || !shellValue) {
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
    // Handled inside EditionFormDialog via useEditions mutations
    void data;
  };

  return (
    <OfferShellContext.Provider value={shellValue}>
      <OfferAutoSaveContext.Provider value={autoSaveValue}>
        <div className="flex h-full flex-col bg-background">
          {/* Topbar — breadcrumb */}
          <header
            className="flex h-[var(--brand-topbar-h,48px)] shrink-0 items-center gap-3 border-b border-border bg-background px-5"
            aria-label="Ruta de Offer Studio"
          >
            <OfferStudioBreadcrumb offerName={offer.name} />
          </header>

          {/* Row 1 — title, status, actions */}
          <OfferShellHeaderRow1 />

          {/* Body row — VariantRail (optional) + right pane */}
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

            {/* Right pane — TabBar + content */}
            <div className="flex min-w-0 min-h-0 flex-1 flex-col">
              <OfferTabBar
                tenantId={tenantId}
                offerId={offerId}
                counts={safeCounts}
                currentEditionId={null}
              />
              <main className="flex-1 overflow-y-auto">{children}</main>
            </div>
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
      </OfferAutoSaveContext.Provider>
    </OfferShellContext.Provider>
  );
}
