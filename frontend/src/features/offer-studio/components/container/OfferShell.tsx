"use client";

import { useMemo, useState } from "react";

import {
  OfferShellContext,
  OfferAutoSaveContext,
  DEFAULT_SNAPSHOT,
} from "../../context/OfferShellContext";
import { useEditions } from "../../hooks/use-editions";
import { useOfferWithEdition } from "../../hooks/use-offer-with-edition";
import { useRailCollapsed } from "../../hooks/use-rail-collapsed";
import { EditionFormDialog } from "../editions/EditionFormDialog";

import { EditionsRail } from "./EditionsRail";
import { EditionsRailCollapsed } from "./EditionsRailCollapsed";
import { OfferShellHeaderRow1 } from "./OfferShellHeaderRow1";
import { OfferTabBar } from "./OfferTabBar";

import type {
  OfferShellContextValue,
  OfferAutoSaveSnapshot,
  OfferAutoSaveContextValue,
} from "../../context/OfferShellContext";
import type { OfferCountsResponse } from "../../types/counts";
import type { LaunchEdition, LaunchEditionCreate, LaunchEditionUpdate, Offer } from "../../types";

export type { OfferAutoSaveSnapshot };

export interface OfferShellProps {
  offer: Offer;
  counts: OfferCountsResponse;
  tenantId: string;
  children: React.ReactNode;
}

/**
 * Persistent Offer Studio shell (v3 layout).
 *
 * Layout:
 *   ┌ Row1 (offer-level: title + status + kebab) ────────────────┐
 *   ├────────────┬──────────────────────────────────────────────┤
 *   │ Rail       │ TabBar (4 tabs + Landing action button)      │
 *   │ (optional) ├──────────────────────────────────────────────┤
 *   │            │ Tab content (children)                        │
 *   └────────────┴──────────────────────────────────────────────┘
 *
 * The rail only renders when `offer.has_editions === true`. The user can
 * collapse it into a 56px badge strip; preference is persisted in
 * localStorage via `useRailCollapsed`. Rail lives inside the offer main
 * area (not sibling of the app sidebar) so the offer header stays the only
 * persistent identifier.
 *
 * The TabBar lives INSIDE the right pane — it belongs to the currently
 * selected edition, not to the whole offer — so it sits next to the rail
 * rather than above it. When the offer has no editions, the right pane
 * fills the width and the TabBar still renders directly under Row1.
 *
 * Row2 (progress bar + global "Autocompletar IA" button) was removed: progress
 * is per-edition (rendered inside the rail entry) and IA completion is a
 * Focus-mode action scoped to the active edition (lives inside the Info tab).
 */
export function OfferShell({ offer, counts, tenantId, children }: OfferShellProps) {
  const [snapshot, setSnapshot] = useState<OfferAutoSaveSnapshot>(DEFAULT_SNAPSHOT);
  const [railCollapsed, toggleRailCollapsed] = useRailCollapsed();

  const [editionFormOpen, setEditionFormOpen] = useState(false);
  const [editionFormSource, setEditionFormSource] = useState<LaunchEdition | undefined>(undefined);

  const showsRail = offer.has_editions === true;
  const { editions, createEdition, updateEdition } = useEditions(showsRail ? offer.id : "");
  const { currentEditionId } = useOfferWithEdition(showsRail ? offer.id : "");

  const shellValue = useMemo<OfferShellContextValue>(
    () => ({ offer, counts, tenantId }),
    [offer, counts, tenantId],
  );

  const autoSaveValue = useMemo<OfferAutoSaveContextValue>(
    () => ({ ...snapshot, setSnapshot }),
    [snapshot],
  );

  const openNewEdition = () => {
    setEditionFormSource(undefined);
    setEditionFormOpen(true);
  };

  const handleEditionSave = async (data: LaunchEditionCreate | LaunchEditionUpdate) => {
    if (editionFormSource) {
      await updateEdition({ editionId: editionFormSource.id, data: data as LaunchEditionUpdate });
    } else {
      await createEdition(data as LaunchEditionCreate);
    }
  };

  return (
    <OfferShellContext.Provider value={shellValue}>
      <OfferAutoSaveContext.Provider value={autoSaveValue}>
        <div className="flex h-full flex-col bg-background">
          <OfferShellHeaderRow1 />

          <div className="flex min-h-0 flex-1">
            {showsRail ? (
              railCollapsed ? (
                <EditionsRailCollapsed
                  offerId={offer.id}
                  tenantId={tenantId}
                  editions={editions}
                  currentEditionId={currentEditionId}
                  onExpand={toggleRailCollapsed}
                  onCreateNew={openNewEdition}
                />
              ) : (
                <EditionsRail
                  offerId={offer.id}
                  tenantId={tenantId}
                  editions={editions}
                  currentEditionId={currentEditionId}
                  onCollapse={toggleRailCollapsed}
                  onCreateNew={openNewEdition}
                />
              )
            ) : null}

            <div className="flex min-w-0 flex-1 flex-col">
              <OfferTabBar tenantId={tenantId} offerId={offer.id} counts={counts} />
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
