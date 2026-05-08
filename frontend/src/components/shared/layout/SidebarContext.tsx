"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  /** Imperatively collapse the sidebar (used by mutex policy). */
  collapseSidebar: () => void;
  /** Imperatively expand the sidebar (used by mutex policy). */
  expandSidebar: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

/**
 * Provides sidebar collapsed state and imperative actions to the component tree.
 *
 * T-4 changes:
 * - Removed inline `useEffect + window.matchMedia(<1279)` auto-collapse logic.
 *   Viewport-aware mutex policy now lives in `useShellMutex` (DashboardShellClient).
 * - Added `expandSidebar()` and `collapseSidebar()` imperative actions so the
 *   mutex hook can drive sidebar state without consumers knowing about matchMedia.
 */
export function SidebarProvider({ children }: { children: React.ReactNode }) {
  // Always start expanded (matches SSR) — sync from localStorage after hydration
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("sidebar-collapsed");
      if (saved === "true") {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: sync localStorage state after SSR hydration
        setIsCollapsed(true);
      }
    } catch {
      // localStorage unavailable
    }
  }, []);

  // NOTE: The inline matchMedia auto-collapse useEffect has been REMOVED in T-4.
  // Viewport-aware collapse is now driven by useShellMutex in DashboardShellClient.

  const toggleSidebar = () => {
    setIsCollapsed((prev: boolean) => {
      const newState = !prev;
      localStorage.setItem("sidebar-collapsed", JSON.stringify(newState));
      return newState;
    });
  };

  const collapseSidebar = () => {
    setIsCollapsed((prev: boolean) => {
      if (prev) return prev; // already collapsed — no-op
      localStorage.setItem("sidebar-collapsed", JSON.stringify(true));
      return true;
    });
  };

  const expandSidebar = () => {
    setIsCollapsed((prev: boolean) => {
      if (!prev) return prev; // already expanded — no-op
      localStorage.setItem("sidebar-collapsed", JSON.stringify(false));
      return false;
    });
  };

  return (
    <SidebarContext.Provider value={{ isCollapsed, toggleSidebar, collapseSidebar, expandSidebar }}>
      {children}
    </SidebarContext.Provider>
  );
}

/**
 *
 */
export function useSidebar() {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
