"use client";

import { Pencil } from "lucide-react";
import { forwardRef, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { useMutationJournal } from "../hooks/use-mutation-journal";
import { usePatchConversation } from "../hooks/use-patch-conversation";
import { useCopilotStore } from "../store/copilot-store";

import { MutationUndoButton } from "./MutationUndoButton";
import { TierChip } from "./TierChip";

import type { ModelTier } from "../types/conversations";

// ── Types ────────────────────────────────────────────────────────────

type CopilotChatHeaderProps = React.HTMLAttributes<HTMLDivElement>;

// ── Helpers ──────────────────────────────────────────────────────────

function getRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "hace un momento";
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.floor(hours / 24);
  return `hace ${days} d`;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Chat panel header with editable title, tier meta, and mutation undo button.
 */
export const CopilotChatHeader = forwardRef<HTMLDivElement, CopilotChatHeaderProps>(
  ({ className, ...props }, ref) => {
    const conversationId = useCopilotStore((s) => s.conversationId);
    const messages = useCopilotStore((s) => s.messages);
    const lastMessageTiers = useCopilotStore((s) => s.lastMessageTiers);

    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    const { mutate: patchConversation } = usePatchConversation();
    const { data: journal } = useMutationJournal(conversationId);

    // Derive last tier from last assistant message
    const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
    const lastTier = lastAssistantMsg
      ? (lastMessageTiers[lastAssistantMsg.id] as ModelTier | undefined)
      : undefined;

    // Derive title from session or generic fallback
    const session = useCopilotStore((s) => s.session);
    const title = session?.label ?? "Chat";

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

    return (
      <div
        ref={ref}
        className={cn("flex flex-col gap-0.5 border-b border-border px-4 py-2.5", className)}
        {...props}
      >
        <div className="flex items-center justify-between gap-2">
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
              className="h-7 text-sm font-semibold flex-1 px-1 py-0"
            />
          ) : (
            <button
              type="button"
              onClick={handleTitleClick}
              className="group flex items-center gap-1 text-sm font-semibold truncate min-w-0 text-left hover:text-foreground/80"
              title="Haz clic para renombrar"
            >
              <span className="truncate">{title}</span>
              <Pencil className="h-3 w-3 shrink-0 opacity-0 group-hover:opacity-40" />
            </button>
          )}

          {/* Mutation undo button */}
          {conversationId && (
            <MutationUndoButton
              conversationId={conversationId}
              mutationCount={journal?.activeCount ?? 0}
            />
          )}
        </div>

        {/* Meta line: last tier + message count */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {lastTier && <TierChip tier={lastTier} size="xs" />}
          {messages.length > 0 && (
            <span>
              {messages.length} {messages.length === 1 ? "mensaje" : "mensajes"}
            </span>
          )}
        </div>
      </div>
    );
  },
);
CopilotChatHeader.displayName = "CopilotChatHeader";

// Suppress unused import warning — getRelativeTime is available for future use
void getRelativeTime;
