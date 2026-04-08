"use client";

import { memo } from "react";
import { PanelRightClose, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";

export const CopilotPanel = memo(function CopilotPanel() {
  useRouteTracker();
  useCopilotNavigator(); // Processes pending UI action queue
  const { isOpen, closePanel, clearMessages } = useCopilotStore();

  return (
    <div className="fixed right-0 top-0 z-[60] flex h-screen">
      {/* Expanded panel */}
      {isOpen ? (
        <div className="flex h-full w-[380px] flex-col border-l border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
          {/* Header */}
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

          {/* Chat body */}
          <CopilotChat />
        </div>
      ) : (
        /* Collapsed rail */
        <CopilotRail />
      )}
    </div>
  );
});
CopilotPanel.displayName = "CopilotPanel";
