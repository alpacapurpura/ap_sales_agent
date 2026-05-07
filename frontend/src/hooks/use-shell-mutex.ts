"use client";

import { useMemo, useEffect } from "react";
import { useStore } from "zustand";

import {
  createShellMutexStore,
  type ActivePanel,
  type ShellMutexActions,
  type ShellMutexState,
  type ShellMutexStoreInstance,
} from "@/stores/shell-mutex-store";

export type { ActivePanel };

export interface UseShellMutexReturn extends ShellMutexState, ShellMutexActions {
  /** True when the app-sidebar panel is the active one */
  isSidebarActive: boolean;
  /** True when the copilot panel is the active one */
  isCopilotActive: boolean;
}

/**
 * React hook that provides shell mutex state and actions for the given tenant.
 *
 * Creates (or reuses) a tenant-namespaced zustand store. Mutex policy
 * effects are gated via `useEffect` so Phase 1 remains a no-op skeleton —
 * actual mutex enforcement activates in T-4.
 *
 * AD4: tenant-namespaced store factory.
 */
export function useShellMutex(tenantId: string): UseShellMutexReturn {
  // useMemo creates a stable store instance per tenantId.
  // When tenantId changes a new store is created (old panel state clears).
  const store = useMemo<ShellMutexStoreInstance>(() => createShellMutexStore(tenantId), [tenantId]);

  const activePanel = useStore(store, (s) => s.activePanel);
  const openPanel = useStore(store, (s) => s.openPanel);
  const closePanel = useStore(store, (s) => s.closePanel);
  const togglePanel = useStore(store, (s) => s.togglePanel);

  // Phase 1: Mutex enforcement effect — GATED, no-op until T-4 activates policy.
  // This useEffect intentionally does nothing in Phase 1.
  // T-4 will add viewport-aware conditions here.
  useEffect(() => {
    // Phase 1: no-op. Mutex policy activation in T-4.
    // Do not remove this block — it reserves the effect slot for T-4.
  }, [activePanel, tenantId]);

  return useMemo(
    () => ({
      activePanel,
      openPanel,
      closePanel,
      togglePanel,
      isSidebarActive: activePanel === "app-sidebar",
      isCopilotActive: activePanel === "copilot",
    }),
    [activePanel, openPanel, closePanel, togglePanel],
  );
}
