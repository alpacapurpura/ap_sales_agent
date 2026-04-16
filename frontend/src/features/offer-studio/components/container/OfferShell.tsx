"use client";

import { useMemo, useState } from "react";

import {
  OfferShellContext,
  OfferAutoSaveContext,
  DEFAULT_SNAPSHOT,
} from "../../context/OfferShellContext";

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
 * Persistent Offer Studio shell: two header rows + tab bar + children.
 *
 * Row 1 (identity + lifecycle), Row 2 (progress + landing + AI) and the tab
 * bar live here once per offer. Next.js layout persistence keeps this tree
 * mounted while `children` swap when the user moves between tabs.
 */
export function OfferShell({ offer, counts, tenantId, children }: OfferShellProps) {
  const [snapshot, setSnapshot] = useState<OfferAutoSaveSnapshot>(DEFAULT_SNAPSHOT);

  const shellValue = useMemo<OfferShellContextValue>(
    () => ({ offer, counts, tenantId }),
    [offer, counts, tenantId],
  );

  const autoSaveValue = useMemo<OfferAutoSaveContextValue>(
    () => ({ ...snapshot, setSnapshot }),
    [snapshot],
  );

  return (
    <OfferShellContext.Provider value={shellValue}>
      <OfferAutoSaveContext.Provider value={autoSaveValue}>
        <div className="flex h-full flex-col bg-background">
          <OfferShellHeaderRow1 />
          <OfferShellHeaderRow2 />
          <OfferTabBar tenantId={tenantId} offerId={offer.id} counts={counts} />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </OfferAutoSaveContext.Provider>
    </OfferShellContext.Provider>
  );
}
