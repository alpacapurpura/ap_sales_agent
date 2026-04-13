"use client";

import { memo } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";
import { CopilotHeader } from "./copilot-header";
import { CopilotPreviewPane } from "./copilot-preview-pane";
import { FocusBar } from "./focus-bar";
import { cn } from "@/lib/utils";

const SIDEBAR_WIDTHS = {
  collapsed: "w-[60px]",
  open: "w-[380px]",
  expanded: "w-[780px]",
} as const;

export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);

  return (
    <aside
      className={cn(
        "flex-shrink-0 h-full overflow-hidden border-l border-slate-200 bg-white",
        "transition-[width] duration-300 ease-in-out",
        "dark:border-slate-700 dark:bg-slate-900",
        SIDEBAR_WIDTHS[sidebarState],
      )}
    >
      {sidebarState === "collapsed" ? (
        <CopilotRail />
      ) : (
        <div className="flex h-full">
          {/* Preview pane — only when expanded */}
          {sidebarState === "expanded" && (
            <div className="w-[400px] shrink-0 border-r border-slate-200 overflow-hidden dark:border-slate-700">
              <CopilotPreviewPane />
            </div>
          )}
          {/* Chat column — always 380px */}
          <div className="flex w-[380px] shrink-0 flex-col">
            <CopilotHeader />
            <FocusBar />
            <CopilotChat />
          </div>
        </div>
      )}
    </aside>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
