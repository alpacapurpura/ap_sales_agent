"use client";

import { memo } from "react";

import { cn } from "@/lib/utils";

import { useCopilotNavigator } from "../hooks/use-copilot-navigator";
import { useRouteTracker } from "../hooks/use-route-tracker";
import { useCopilotStore } from "../store/copilot-store";

import { CopilotChat } from "./CopilotChat";
import { CopilotHeader } from "./CopilotHeader";
import { CopilotRail } from "./CopilotRail";

// ── Width classes for md+ screens ────────────────────────────────────
const SIDEBAR_WIDTHS = {
  collapsed: "md:w-[60px]",
  open: "md:w-[380px]",
} as const;

/**
 * Sidebar container for the copilot. Sprint 4a simplifies the layout:
 * the legacy dual-column preview + chat split died with the preview pane
 * (see DECISIONS.md D5). Sidebar is now chat-only and toggles between the
 * collapsed rail (desktop) and a full-height chat column.
 */
export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);

  const isOpen = sidebarState !== "collapsed";

  return (
    <>
      {/* ── Mobile backdrop overlay ────────────────────────────────── */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar container ─────────────────────────────────────── */}
      <aside
        data-testid="copilot-sidebar"
        className={cn(
          // Base layout
          "flex-shrink-0 h-full overflow-hidden border-l border-slate-200 bg-white",
          "dark:border-slate-700 dark:bg-slate-900",
          // Smooth width transition on md+
          "transition-[width] duration-300 ease-in-out",
          // Mobile: fixed full-screen overlay when open, hidden when collapsed
          "max-md:fixed max-md:inset-y-0 max-md:right-0 max-md:z-50 max-md:w-full max-md:border-l-0 max-md:shadow-2xl",
          isOpen ? "max-md:translate-x-0" : "max-md:translate-x-full",
          "max-md:transition-transform max-md:duration-300 max-md:ease-in-out",
          // Desktop widths
          SIDEBAR_WIDTHS[sidebarState],
        )}
      >
        {sidebarState === "collapsed" ? (
          /* ── Rail (collapsed desktop) — hidden on mobile ──────── */
          <div className="hidden md:flex md:h-full">
            <CopilotRail />
          </div>
        ) : (
          /* ── Chat column ─────────────────────────────────────── */
          <div className="flex h-full flex-col">
            <CopilotHeader />
            <CopilotChat />
          </div>
        )}
      </aside>
    </>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
