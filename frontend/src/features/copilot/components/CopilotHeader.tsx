"use client";

import { PanelRightClose, RotateCcw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useCopilotStore } from "../store/copilot-store";

import type { CopilotSession } from "../store/copilot-store";

/**
 * Header label derived from the current session. ``free`` sessions surface
 * the entity label; ``guided`` sessions prefix with "Guía:" and show a
 * compact "Bloque N/M" chip. No active session falls back to "Chat".
 */
function getModeLabel(session: CopilotSession | null): string {
  if (!session) return "Chat";
  if (session.procedure === "guided") {
    return `Guía: ${session.label}`;
  }
  return session.label;
}

function getProgressText(session: CopilotSession | null): string | null {
  if (session?.procedure !== "guided" || !session.progress) return null;
  const { totalBlocks, blocksCompleted, currentBlock } = session.progress;
  if (!totalBlocks) return null;
  const index = blocksCompleted.length + (currentBlock ? 1 : 0);
  const suffix = currentBlock?.label ? ` · ${currentBlock.label}` : "";
  return `Bloque ${Math.min(index, totalBlocks)}/${totalBlocks}${suffix}`;
}

/**
 * Copilot panel header. Adds a subtle purple accent when a guided session is
 * active so the user has a persistent visual cue without a dedicated mode UI.
 */
export function CopilotHeader() {
  const session = useCopilotStore((s) => s.session);
  const closePanel = useCopilotStore((s) => s.closePanel);
  const resetConversation = useCopilotStore((s) => s.resetConversation);

  const modeLabel = getModeLabel(session);
  const progress = getProgressText(session);
  const isGuided = session?.procedure === "guided";

  return (
    <div
      className={cn(
        "flex items-center justify-between border-b px-4 py-3",
        isGuided
          ? "border-purple-500/40 bg-purple-500/5 dark:border-purple-400/40 dark:bg-purple-500/10"
          : "border-slate-200 dark:border-slate-700",
      )}
    >
      <div className="flex min-w-0 flex-col">
        <div className="flex items-center gap-2 min-w-0">
          <Sparkles
            className={cn(
              "h-4 w-4 shrink-0",
              isGuided
                ? "text-purple-500 dark:text-purple-300"
                : "text-purple-600 dark:text-purple-400",
            )}
          />
          <span className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
            {modeLabel}
          </span>
        </div>
        {progress && (
          <span className="ml-6 truncate text-xs text-purple-600 dark:text-purple-300">
            {progress}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1">
        <Button
          size="icon"
          variant="ghost"
          onClick={resetConversation}
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
