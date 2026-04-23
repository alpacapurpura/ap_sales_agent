"use client";

import { PanelRightClose, Pencil, PanelRightOpen, Sparkles, X } from "lucide-react";
import { forwardRef, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { useMutationJournal } from "../hooks/use-mutation-journal";
import { usePatchConversation } from "../hooks/use-patch-conversation";
import { useCopilotStore } from "../store/copilot-store";

import { MutationUndoButton } from "./MutationUndoButton";
import { TierChip } from "./TierChip";

import type { ModelTier } from "../types/conversations";

type CopilotChatHeaderProps = React.HTMLAttributes<HTMLDivElement>;

export const CopilotChatHeader = forwardRef<HTMLDivElement, CopilotChatHeaderProps>(
  ({ className, ...props }, ref) => {
    const conversationId = useCopilotStore((s) => s.conversationId);
    const messages = useCopilotStore((s) => s.messages);
    const lastMessageTiers = useCopilotStore((s) => s.lastMessageTiers);
    const sidebarState = useCopilotStore((s) => s.sidebarState);
    const setSidebarState = useCopilotStore((s) => s.setSidebarState);
    const session = useCopilotStore((s) => s.session);

    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    const { mutate: patchConversation } = usePatchConversation();
    const { data: journal } = useMutationJournal(conversationId);

    const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
    const lastTier = lastAssistantMsg
      ? (lastMessageTiers[lastAssistantMsg.id] as ModelTier | undefined)
      : undefined;

    const title = session?.label ?? "Chat";
    const isFull = sidebarState === "full";

    const handleTitleClick = () => {
      setEditValue(title);
      setIsEditing(true);
      setTimeout(() => inputRef.current?.select(), 0);
    };

    const handleRenameSubmit = () => {
      const trimmed = editValue.trim();
      if (trimmed && trimmed !== title && conversationId) {
        patchConversation({ id: conversationId, body: { title: trimmed } });
      }
      setIsEditing(false);
    };

    const handleRenameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleRenameSubmit();
      } else if (e.key === "Escape") {
        setIsEditing(false);
      }
    };

    const toggleHistory = () => setSidebarState(isFull ? "rail" : "full");
    const closeCopilot = () => setSidebarState("collapsed");

    return (
      <TooltipProvider delayDuration={200}>
        <div
          ref={ref}
          className={cn("flex h-12 items-center gap-2 border-b border-border px-3", className)}
          {...props}
        >
          {/* Sparkles avatar */}
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand/15">
            <Sparkles className="h-3.5 w-3.5 text-brand" aria-hidden="true" />
          </div>

          {/* Title (editable) */}
          {isEditing ? (
            <Input
              ref={inputRef}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={handleRenameKeyDown}
              maxLength={120}
              autoFocus
              className="h-7 min-w-0 flex-1 px-1.5 py-0 text-sm font-semibold"
            />
          ) : (
            <button
              type="button"
              onClick={handleTitleClick}
              className="group flex min-w-0 flex-1 items-center gap-1.5 truncate rounded-md px-1.5 py-1 text-left text-sm font-semibold hover:bg-muted/50"
              title="Haz clic para renombrar"
            >
              <span className="truncate">{title}</span>
              <Pencil className="h-3 w-3 shrink-0 opacity-0 transition group-hover:opacity-40" />
            </button>
          )}

          {/* Tier + count chip */}
          {(lastTier ?? messages.length > 0) && (
            <div className="hidden items-center gap-1.5 rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline-flex">
              {lastTier && <TierChip tier={lastTier} size="xs" />}
              {messages.length > 0 && (
                <span>
                  {messages.length} {messages.length === 1 ? "msg" : "msgs"}
                </span>
              )}
            </div>
          )}

          {/* Mutation undo button */}
          {conversationId && (
            <MutationUndoButton
              conversationId={conversationId}
              mutationCount={journal?.activeCount ?? 0}
            />
          )}

          <span className="mx-1 h-5 w-px bg-border" />

          {/* Toggle historial */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={toggleHistory}
                aria-label={isFull ? "Ocultar historial" : "Mostrar historial"}
                className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
              >
                {isFull ? (
                  <PanelRightClose className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  <PanelRightOpen className="h-3.5 w-3.5" aria-hidden="true" />
                )}
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {isFull ? "Ocultar historial" : "Mostrar historial"}
            </TooltipContent>
          </Tooltip>

          {/* Close copilot */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={closeCopilot}
                aria-label="Cerrar copilot"
                className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Cerrar copilot</TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
    );
  },
);
CopilotChatHeader.displayName = "CopilotChatHeader";
