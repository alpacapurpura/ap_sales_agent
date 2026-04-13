"use client";

import { memo } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";
import { cn } from "@/lib/utils";
import { Sparkles, PanelRightClose, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

const SIDEBAR_WIDTHS = {
  collapsed: "w-[60px]",
  open: "w-[380px]",
  expanded: "w-[780px]",
} as const;

export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const closePanel = useCopilotStore((s) => s.closePanel);
  const clearMessages = useCopilotStore((s) => s.clearMessages);

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
        <div className="flex h-full flex-col">
          {/* Temporary header — replaced by CopilotHeader in Task 7 */}
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Copilot
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                size="icon"
                variant="ghost"
                onClick={clearMessages}
                className="h-7 w-7 text-slate-400 hover:text-slate-600"
                title="Nueva conversación"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={closePanel}
                className="h-7 w-7 text-slate-400 hover:text-slate-600"
              >
                <PanelRightClose className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <CopilotChat />
        </div>
      )}
    </aside>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
