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

import { EditionsRail } from "./EditionsRail";
import { EditionsRailCollapsed } from "./EditionsRailCollapsed";
import { OfferShellHeaderRow1 } from "./OfferShellHeaderRow1";
import { OfferShellHeaderRow2 } from "./OfferShellHeaderRow2";
import { OfferTabBar } from "./OfferTabBar";

import type {
  OfferShellContextValue,
  OfferAutoSaveSnapshot,
  OfferAutoSaveContextValue,
} from "../../context/OfferShellContext";
import type { OfferCountsResponse } from "../../types/counts";
import type { Offer } from "@/features/offer-studio/types";

export type { OfferAutoSaveSnapshot };

export interface OfferShellProps {
  offer: Offer;
  counts: OfferCountsResponse;
  tenantId: string;
  children: React.ReactNode;
}

/**
 * Persistent Offer Studio shell: optional editions rail + header rows +
 * tab bar + children.
 *
 * The rail only renders when `offer.has_editions === true`. The user
 * can collapse it into a 56px badge strip; preference is persisted in
 * localStorage via `useRailCollapsed`. When collapsed the main pane
 * still resolves the current edition from the URL so the content of
 * each tab stays in sync with the badge highlight.
 */
export function OfferShell({ offer, counts, tenantId, children }: OfferShellProps) {
  const [snapshot, setSnapshot] = useState<OfferAutoSaveSnapshot>(DEFAULT_SNAPSHOT);
  const [railCollapsed, toggleRailCollapsed] = useRailCollapsed();

  const showsRail = offer.has_editions === true;
  const { editions } = useEditions(showsRail ? offer.id : "");
  const { currentEditionId } = useOfferWithEdition(showsRail ? offer.id : "");

  const shellValue = useMemo<OfferShellContextValue>(
    () => ({ offer, counts, tenantId }),
    [offer, counts, tenantId],
  );

  const autoSaveValue = useMemo<OfferAutoSaveContextValue>(
    () => ({ ...snapshot, setSnapshot }),
    [snapshot],
  );

  const openCloneModal = () => {
    // Clone modal arrives in Phase 9a part 2; the rail's CTAs still have
    // to be clickable so we emit a no-op toast-like log until the modal
    // is wired. The console hint gives developers a trail during dev.
    console.info("[offer-studio] EditionCloneModal pending — Phase 9a part 2");
  };

  return (
    <OfferShellContext.Provider value={shellValue}>
      <OfferAutoSaveContext.Provider value={autoSaveValue}>
        <div className="flex h-full bg-background">
          {showsRail ? (
            railCollapsed ? (
              <EditionsRailCollapsed
                offerId={offer.id}
                tenantId={tenantId}
                editions={editions}
                currentEditionId={currentEditionId}
                onExpand={toggleRailCollapsed}
                onCreateNew={openCloneModal}
              />
            ) : (
              <EditionsRail
                offerId={offer.id}
                offerName={offer.name}
                tenantId={tenantId}
                editions={editions}
                currentEditionId={currentEditionId}
                onCollapse={toggleRailCollapsed}
                onCreateNew={openCloneModal}
              />
            )
          ) : null}

          <div className="flex h-full flex-1 flex-col">
            <OfferShellHeaderRow1 />
            <OfferShellHeaderRow2 />
            <OfferTabBar tenantId={tenantId} offerId={offer.id} counts={counts} />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </OfferAutoSaveContext.Provider>
    </OfferShellContext.Provider>
  );
}
