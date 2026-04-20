"use client";

import { PanelRightClose, RotateCcw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useCopilotStore } from "../store/copilot-store";

import type { CopilotSession } from "../store/copilot-store";

/**
 * Header label derived from the current session. ``free`` sessions surface
 * the entity label; ``interview`` sessions prefix with "Entrevista:". No
 * active session falls back to the generic "Chat" label.
 */
function getModeLabel(session: CopilotSession | null): string {
  if (!session) return "Chat";
  if (session.procedure === "interview") {
    return `Entrevista: ${session.label}`;
  }
  return session.label;
}

/**
 *
 */
export function CopilotHeader() {
  const session = useCopilotStore((s) => s.session);
  const closePanel = useCopilotStore((s) => s.closePanel);
  const clearMessages = useCopilotStore((s) => s.clearMessages);

  const modeLabel = getModeLabel(session);

  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
      <div className="flex items-center gap-2 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
        <span className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
          {modeLabel}
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
          title="Cerrar"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
