"use client";

import { Maximize2, Minimize2, PanelRightClose, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import type { SidebarState } from "../store/copilot-store";

function getModeLabel(state: {
  interviewSessionId: string | null;
  focusEntity: { domain: string; label: string } | null;
}): string {
  if (state.interviewSessionId) {
    return `Entrevista: ${state.focusEntity?.label ?? ""}`;
  }
  if (state.focusEntity) {
    return `Focus: ${state.focusEntity.label}`;
  }
  return "Chat";
}

export function CopilotHeader() {
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const interviewSessionId = useCopilotStore((s) => s.interviewSessionId);
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const closePanel = useCopilotStore((s) => s.closePanel);
  const clearMessages = useCopilotStore((s) => s.clearMessages);

  const modeLabel = getModeLabel({ interviewSessionId, focusEntity });
  const canExpand = sidebarState === "open" && focusEntity;
  const canCollapse = sidebarState === "expanded";

  const handleToggleExpand = () => {
    const next: SidebarState = sidebarState === "expanded" ? "open" : "expanded";
    setSidebarState(next);
  };

  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
      <div className="flex items-center gap-2 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
        <span className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
          {modeLabel}
        </span>
      </div>
      <div className="flex items-center gap-1">
        {(canExpand || canCollapse) && (
          <Button
            size="icon"
            variant="ghost"
            onClick={handleToggleExpand}
            className="h-7 w-7 text-slate-400 hover:text-slate-600"
            title={canExpand ? "Expandir" : "Contraer"}
          >
            {canExpand ? (
              <Maximize2 className="h-3.5 w-3.5" />
            ) : (
              <Minimize2 className="h-3.5 w-3.5" />
            )}
          </Button>
        )}
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
          title="Cerrar"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
