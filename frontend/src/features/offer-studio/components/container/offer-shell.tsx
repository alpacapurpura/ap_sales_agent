"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { Offer } from "@/features/offer-studio/types";
import type { OfferCountsResponse } from "../../types/counts";
import type { AutoSaveState } from "../../hooks/use-auto-save";
import { OfferShellHeaderRow1 } from "./offer-shell-header-row1";
import { OfferShellHeaderRow2 } from "./offer-shell-header-row2";
import { OfferTabBar } from "./offer-tab-bar";

/**
 * Shared context exposing the offer, counts and tenant id to every widget
 * inside the persistent shell. Tabs read from here instead of refetching.
 */
interface OfferShellContextValue {
  offer: Offer;
  counts: OfferCountsResponse;
  tenantId: string;
}

const OfferShellContext = createContext<OfferShellContextValue | null>(null);

export function useOfferShell(): OfferShellContextValue {
  const ctx = useContext(OfferShellContext);
  if (!ctx) {
    throw new Error("useOfferShell must be used within an <OfferShell> provider.");
  }
  return ctx;
}

/**
 * Autosave context — the editor (FE Chunk 3) pushes its mutation state here
 * so the header's <AutoSaveIndicator /> can render without prop drilling.
 *
 * For Chunk 2b this defaults to `idle` — wiring is done in the next chunk.
 */
export interface OfferAutoSaveSnapshot {
  state: AutoSaveState;
  lastSavedAt: Date | null;
  errorMessage?: string;
  onRetry?: () => void;
}

interface OfferAutoSaveContextValue extends OfferAutoSaveSnapshot {
  setSnapshot: (snapshot: OfferAutoSaveSnapshot) => void;
}

const DEFAULT_SNAPSHOT: OfferAutoSaveSnapshot = {
  state: "idle",
  lastSavedAt: null,
};

const OfferAutoSaveContext = createContext<OfferAutoSaveContextValue | null>(null);

export function useOfferAutoSave(): OfferAutoSaveContextValue {
  const ctx = useContext(OfferAutoSaveContext);
  if (!ctx) {
    // Safe fallback: if a consumer renders outside the provider, the indicator
    // simply stays idle instead of throwing. Keeps the shell forgiving.
    return {
      ...DEFAULT_SNAPSHOT,
      setSnapshot: () => {},
    };
  }
  return ctx;
}

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
