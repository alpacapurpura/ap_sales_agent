"use client";

import { MessageSquare, Eye } from "lucide-react";
import { memo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotStore } from "../store/copilot-store";

import { CopilotHeader } from "./copilot-header";
import { CopilotPreviewPane } from "./copilot-preview-pane";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";
import { FocusBar } from "./focus-bar";

// ── Width classes for md+ screens ────────────────────────────────────
const SIDEBAR_WIDTHS = {
  collapsed: "md:w-[60px]",
  open: "md:w-[380px]",
  expanded: "md:w-[780px]",
} as const;

// ── Mobile toggle button (chat ↔ preview) ─────────────────────────────
type MobileView = "chat" | "preview";

interface MobileViewToggleProps {
  view: MobileView;
  onToggle: () => void;
}

function MobileViewToggle({ view, onToggle }: MobileViewToggleProps) {
  return (
    <div className="flex shrink-0 items-center gap-1 border-b border-slate-200 px-4 py-2 dark:border-slate-700 md:hidden">
      <Button
        size="sm"
        variant={view === "chat" ? "secondary" : "ghost"}
        onClick={() => view !== "chat" && onToggle()}
        className="h-7 gap-1.5 text-xs"
      >
        <MessageSquare className="h-3.5 w-3.5" />
        Chat
      </Button>
      <Button
        size="sm"
        variant={view === "preview" ? "secondary" : "ghost"}
        onClick={() => view !== "preview" && onToggle()}
        className="h-7 gap-1.5 text-xs"
      >
        <Eye className="h-3.5 w-3.5" />
        Vista previa
      </Button>
    </div>
  );
}

export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const [mobileView, setMobileView] = useState<MobileView>("chat");

  const isOpen = sidebarState !== "collapsed";
  const isExpanded = sidebarState === "expanded";

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
          <div className="flex h-full flex-col md:flex-row">
            {/* ── Mobile toggle bar (only in expanded state) ───────── */}
            {isExpanded && (
              <MobileViewToggle
                view={mobileView}
                onToggle={() => setMobileView((v) => (v === "chat" ? "preview" : "chat"))}
              />
            )}

            {/* ── Inner content row ─────────────────────────────── */}
            <div className="flex min-h-0 flex-1 flex-col md:flex-row">
              {/* Preview pane — desktop: always visible when expanded
                             — mobile:  visible only when mobileView === "preview" */}
              {isExpanded && (
                <div
                  className={cn(
                    "shrink-0 overflow-hidden border-slate-200 dark:border-slate-700",
                    // Desktop: fixed width + right border
                    "md:w-[400px] md:border-r",
                    // Mobile: full width, animated fade+slide
                    "w-full transition-all duration-200 ease-in-out",
                    mobileView === "preview"
                      ? "max-md:flex max-md:opacity-100 max-md:translate-x-0"
                      : "max-md:hidden max-md:opacity-0 max-md:translate-x-4",
                    // Desktop: always visible
                    "md:flex md:opacity-100 md:translate-x-0",
                  )}
                >
                  <CopilotPreviewPane />
                </div>
              )}

              {/* Chat column — desktop: fixed 380px
                            — mobile: full width, animated fade+slide */}
              <div
                className={cn(
                  "flex flex-col",
                  // Desktop: fixed width
                  "md:w-[380px] md:shrink-0",
                  // Mobile: full width, animated
                  "w-full transition-all duration-200 ease-in-out",
                  isExpanded && mobileView === "preview"
                    ? "max-md:hidden max-md:opacity-0 max-md:-translate-x-4"
                    : "max-md:flex max-md:opacity-100 max-md:translate-x-0",
                )}
              >
                <CopilotHeader />
                <FocusBar />
                <CopilotChat />
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
