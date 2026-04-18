"use client";

import { createContext, useContext } from "react";

import type { OfferCountsResponse } from "../types/counts";
import type { Offer } from "@/features/offer-studio/types";
import type { AutoSaveState } from "@/lib/form-runtime/hooks";

// ── Offer Shell Context ──────────────────────────────────────────────────────

export interface OfferShellContextValue {
  offer: Offer;
  counts: OfferCountsResponse;
  tenantId: string;
}

export const OfferShellContext = createContext<OfferShellContextValue | null>(null);

/**
 *
 */
export function useOfferShell(): OfferShellContextValue {
  const ctx = useContext(OfferShellContext);
  if (!ctx) {
    throw new Error("useOfferShell must be used within an <OfferShell> provider.");
  }
  return ctx;
}

// ── Auto Save Context ────────────────────────────────────────────────────────

export interface OfferAutoSaveSnapshot {
  state: AutoSaveState;
  lastSavedAt: Date | null;
  errorMessage?: string;
  onRetry?: () => void;
}

export interface OfferAutoSaveContextValue extends OfferAutoSaveSnapshot {
  setSnapshot: (snapshot: OfferAutoSaveSnapshot) => void;
}

export const DEFAULT_SNAPSHOT: OfferAutoSaveSnapshot = {
  state: "idle",
  lastSavedAt: null,
};

export const OfferAutoSaveContext = createContext<OfferAutoSaveContextValue | null>(null);

/**
 *
 */
export function useOfferAutoSave(): OfferAutoSaveContextValue {
  const ctx = useContext(OfferAutoSaveContext);
  if (!ctx) {
    return {
      ...DEFAULT_SNAPSHOT,
      setSnapshot: () => {},
    };
  }
  return ctx;
}
