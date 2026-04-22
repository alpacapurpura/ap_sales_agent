"use client";

import { memo, useEffect } from "react";

import { cn } from "@/lib/utils";

import { useCopilotNavigator } from "../hooks/use-copilot-navigator";
import { useCreateConversation } from "../hooks/use-create-conversation";
import { useRouteTracker } from "../hooks/use-route-tracker";
import { loadPersistedSidebarState, useCopilotStore } from "../store/copilot-store";

import { CopilotChatPanel } from "./CopilotChatPanel";
import { CopilotHistoryPanel } from "./CopilotHistoryPanel";
import { CopilotRail } from "./CopilotRail";

// ── Component ────────────────────────────────────────────────────────

/**
 * Root copilot sidebar container.
 * Uses a CSS grid with 3 columns: history | chat | rail.
 * State-driven column widths, animated via CSS transitions.
 * Persists sidebarState to localStorage.
 */
export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();

  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const cycleSidebarState = useCopilotStore((s) => s.cycleSidebarState);

  const { mutate: createConversation } = useCreateConversation();

  // Restore persisted state on mount
  useEffect(() => {
    const persisted = loadPersistedSidebarState();
    setSidebarState(persisted);
  }, [setSidebarState]);

  // Keyboard shortcuts (document-level, skip if focus in input/textarea)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const inInput =
        target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable;

      if (e.ctrlKey || e.metaKey) {
        if (e.key === "k") {
          e.preventDefault();
          document.getElementById("copilot-input")?.focus();
        }
        return;
      }

      if (inInput) return;

      switch (e.key) {
        case "C":
          setSidebarState("collapsed");
          break;
        case "R":
          setSidebarState("rail");
          break;
        case "F":
          setSidebarState("full");
          break;
        case "N":
          createConversation();
          break;
        default:
          break;
      }

      void cycleSidebarState; // available for future use
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [setSidebarState, cycleSidebarState, createConversation]);

  // CSS variable values per state — 2-column grid: [chat][rail]
  // "full" state: history panel is rendered inside the chat column (overlay-like) or
  // the grid expands: history (280px) + chat (400px) without a 3rd rail column when full.
  // Spec §1: collapsed=[0, 60px], rail=[400px, 60px], full=[400px, 280px]
  // In "full" state the rail is hidden (controls migrate to history panel header).
  const chatW = sidebarState === "collapsed" ? "0px" : "400px";
  const railOrHistoryW = sidebarState === "full" ? "280px" : "60px";

  const isExpanded = sidebarState !== "collapsed";

  return (
    <>
      {/* Live region for a11y announcements */}
      <span
        role="status"
        aria-live="polite"
        className="sr-only"
        aria-label={
          sidebarState === "collapsed"
            ? "Copilot cerrado"
            : sidebarState === "rail"
              ? "Copilot abierto"
              : "Copilot con historial"
        }
      />

      {/* Mobile backdrop */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
          aria-hidden="true"
          onClick={() => setSidebarState("collapsed")}
        />
      )}

      {/* Sidebar root — CSS grid */}
      <aside
        data-testid="copilot-sidebar"
        aria-expanded={isExpanded}
        aria-label="Panel copilot"
        className={cn(
          "flex-shrink-0 h-full overflow-hidden",
          "transition-[grid-template-columns] duration-[220ms]",
          // Mobile: fixed overlay when open
          "max-md:fixed max-md:inset-y-0 max-md:right-0 max-md:z-50",
          isExpanded ? "max-md:translate-x-0" : "max-md:translate-x-full",
          "max-md:transition-transform max-md:duration-300",
        )}
        style={{
          display: "grid",
          gridTemplateColumns: `${chatW} ${railOrHistoryW}`,
          transition: "grid-template-columns 220ms cubic-bezier(.2,.8,.2,1)",
        }}
      >
        {/* Chat panel — visible in rail and full states */}
        {sidebarState !== "collapsed" ? (
          <CopilotChatPanel />
        ) : (
          <div style={{ width: chatW, overflow: "hidden" }} aria-hidden="true" />
        )}

        {/* Second column: Rail (collapsed/rail) or History panel (full) */}
        {sidebarState === "full" ? <CopilotHistoryPanel /> : <CopilotRail />}
      </aside>
    </>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
