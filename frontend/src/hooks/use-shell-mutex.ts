"use client";

import { useMemo, useEffect } from "react";
import { useStore } from "zustand";

import { useSidebar } from "@/components/shared/layout/SidebarContext";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { useViewport } from "@/hooks/use-viewport";
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
 * effects fire based on viewport breakpoint:
 *
 * - Desktop ≥1280px: both panels independent — no auto-collapse.
 * - Tablet 768-1279px: when copilot opens, sidebar auto-collapses (80px rail).
 * - Mobile <768px: strict mutex — only one drawer at a time.
 *
 * AD2: Mutex breakpoint ≥1280px — both expanded no-mutex allowed.
 * AD4: tenant-namespaced store factory.
 *
 * Must be called inside `SidebarProvider` (needs `useSidebar()`).
 */
export function useShellMutex(tenantId: string): UseShellMutexReturn {
  // useMemo creates a stable store instance per tenantId.
  // When tenantId changes a new store is created (old panel state clears).
  const store = useMemo<ShellMutexStoreInstance>(() => createShellMutexStore(tenantId), [tenantId]);

  const activePanel = useStore(store, (s) => s.activePanel);
  const openPanel = useStore(store, (s) => s.openPanel);
  const closePanel = useStore(store, (s) => s.closePanel);
  const togglePanel = useStore(store, (s) => s.togglePanel);

  // Viewport breakpoint awareness
  const viewport = useViewport();

  // Sidebar imperative actions (from SidebarContext — must be inside SidebarProvider)
  const { collapseSidebar, expandSidebar } = useSidebar();

  // Copilot store — to collapse copilot panel when mutex requires it
  const setCopilotSidebarState = useCopilotStore((s) => s.setSidebarState);

  // ── Mutex policy effect ────────────────────────────────────────────────────
  // Runs when activePanel changes. Applies viewport-aware auto-collapse policy.
  useEffect(() => {
    // Desktop ≥1280px: both panels are independent — no auto-collapse.
    if (viewport.isDesktop) {
      return;
    }

    // Tablet 768-1279px: when copilot opens, sidebar auto-collapses to 80px rail.
    // Sidebar opening does NOT force copilot closed at tablet width.
    if (viewport.isTablet) {
      if (activePanel === "copilot") {
        collapseSidebar();
      }
      return;
    }

    // Mobile <768px: strict mutex — only one drawer at a time.
    if (viewport.isMobile) {
      if (activePanel === "copilot") {
        // Copilot opened → collapse sidebar
        collapseSidebar();
      } else if (activePanel === "app-sidebar") {
        // Sidebar drawer opened → close copilot
        setCopilotSidebarState("collapsed");
      }
    }
  }, [
    activePanel,
    viewport.isDesktop,
    viewport.isTablet,
    viewport.isMobile,
    collapseSidebar,
    expandSidebar,
    setCopilotSidebarState,
  ]);

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
