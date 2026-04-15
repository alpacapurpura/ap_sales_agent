"use client";

import { createContext, useContext, useCallback, type ReactNode } from "react";

import { useSyncAllSources } from "../hooks/useSyncAllSources";

import type { SyncAllResponse } from "../api/metrics-api";

interface GrowthSyncContextValue {
  startSync: (days?: number) => void;
  isSyncing: boolean;
  syncResult: SyncAllResponse | undefined;
  syncError: Error | null;
  resetSync: () => void;
}

const GrowthSyncContext = createContext<GrowthSyncContextValue | null>(null);

export function useGrowthSync() {
  const ctx = useContext(GrowthSyncContext);
  if (!ctx) throw new Error("useGrowthSync must be used inside GrowthSyncProvider");
  return ctx;
}

export function GrowthSyncProvider({ children }: { children: ReactNode }) {
  const { trigger, isLoading, result, error, reset } = useSyncAllSources();

  const startSync = useCallback(
    (days = 30) => {
      trigger(days);
    },
    [trigger],
  );

  const syncError = error instanceof Error ? error : error ? new Error(String(error)) : null;

  return (
    <GrowthSyncContext.Provider
      value={{
        startSync,
        isSyncing: isLoading,
        syncResult: result,
        syncError,
        resetSync: reset,
      }}
    >
      {children}
    </GrowthSyncContext.Provider>
  );
}
