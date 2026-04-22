"use client";

import { MoreHorizontal, Target } from "lucide-react";
import { forwardRef, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { useConversationGroups } from "../hooks/use-conversation-groups";
import { useConversationList } from "../hooks/use-conversation-list";
import { useCreateConversation } from "../hooks/use-create-conversation";
import { useDeleteConversation } from "../hooks/use-delete-conversation";
import { usePatchConversation } from "../hooks/use-patch-conversation";
import { useCopilotStore } from "../store/copilot-store";

import { TierChip } from "./TierChip";

import type { ConversationSummary } from "../types/conversations";

// ── Types ────────────────────────────────────────────────────────────

type CopilotHistoryPanelProps = React.HTMLAttributes<HTMLDivElement>;

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

// ── Conversation item component ──────────────────────────────────────

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onSelect: (id: string) => void;
}

function ConversationItem({ conversation, isActive, onSelect }: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const { mutate: patchConversation } = usePatchConversation();
  const { mutate: deleteConversation } = useDeleteConversation();

  const title = conversation.title ?? "Nueva conversación";

  const handleStartRename = () => {
    setEditValue(title);
    setIsEditing(true);
    setTimeout(() => inputRef.current?.select(), 0);
  };

  const handleRenameSubmit = () => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== title) {
      patchConversation({ id: conversation.id, body: { title: trimmed } });
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

  const handleArchive = () => {
    deleteConversation(conversation.id);
  };

  return (
    <div
      className={cn(
        "group relative flex flex-col gap-0.5 rounded-md px-2 py-1.5 cursor-pointer transition-colors",
        isActive
          ? "bg-accent/10 border-l-2 border-accent rounded-r-md pl-[6px]"
          : "hover:bg-muted/60",
      )}
      onClick={() => !isEditing && onSelect(conversation.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!isEditing) onSelect(conversation.id);
        }
      }}
      onDoubleClick={handleStartRename}
      aria-current={isActive ? "true" : undefined}
    >
      {/* Title row */}
      <div className="flex items-center gap-1 min-w-0">
        {conversation.hasProcedure && (
          <Target className="h-3 w-3 shrink-0 text-muted-foreground/60" />
        )}

        {isEditing ? (
          <Input
            ref={inputRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={handleRenameKeyDown}
            maxLength={120}
            autoFocus
            className="h-6 text-xs px-1 py-0 flex-1"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="truncate text-sm text-foreground">{title}</span>
        )}

        {/* Kebab menu — visible on hover */}
        {!isEditing && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="ml-auto h-5 w-5 shrink-0 opacity-0 group-hover:opacity-100"
                onClick={(e) => e.stopPropagation()}
                aria-label="Opciones de conversación"
              >
                <MoreHorizontal className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="right">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  handleStartRename();
                }}
              >
                Renombrar
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  handleArchive();
                }}
                className="text-destructive focus:text-destructive"
              >
                Archivar
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
        <span>{getRelativeTime(conversation.updatedAt)}</span>
        {conversation.lastTierUsed && (
          <>
            <span>·</span>
            <TierChip tier={conversation.lastTierUsed} size="xs" />
          </>
        )}
        <span>·</span>
        <span>{conversation.messageCount}</span>
        {conversation.hasProcedure && conversation.procedureProgress !== null && (
          <>
            <span>·</span>
            <span className="font-medium text-accent">
              {Math.round((conversation.procedureProgress ?? 0) * 100)}%
            </span>
          </>
        )}
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────

/**
 * History panel with date-grouped conversation list.
 * Visible only when sidebarState === "full".
 */
export const CopilotHistoryPanel = forwardRef<HTMLDivElement, CopilotHistoryPanelProps>(
  ({ className, ...props }, ref) => {
    const conversationId = useCopilotStore((s) => s.conversationId);
    const setConversationId = useCopilotStore((s) => s.setConversationId);
    const clearMessages = useCopilotStore((s) => s.clearMessages);

    const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage, refetch } =
      useConversationList({ limit: 6 });

    const { mutate: createConversation } = useCreateConversation();

    // Flatten all pages
    const allItems = data?.pages.flatMap((page) => page.items) ?? [];
    const groups = useConversationGroups(allItems);

    const handleSelect = (id: string) => {
      setConversationId(id);
      clearMessages();
      // TODO: load conversation messages when endpoint is available
      setTimeout(() => document.getElementById("copilot-input")?.focus(), 50);
    };

    return (
      <div
        ref={ref}
        className={cn(
          "flex h-full w-[280px] flex-col border-r border-border bg-background",
          className,
        )}
        {...props}
      >
        {/* Panel title */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold">Conversaciones</h2>
        </div>

        {/* New conversation button */}
        <div className="px-3 py-2 border-b border-border">
          <Button
            className="w-full justify-start gap-2 text-sm"
            size="sm"
            onClick={() => createConversation()}
          >
            + Nueva conversación
          </Button>
        </div>

        {/* Conversation list */}
        <ScrollArea className="flex-1 px-2">
          <div className="py-2">
            {isLoading && (
              <div className="space-y-2 px-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full rounded-md" />
                ))}
              </div>
            )}

            {isError && (
              <div className="px-2 py-4">
                <Alert>
                  <AlertDescription className="text-xs">
                    No se pudo cargar el historial.{" "}
                    <button
                      type="button"
                      onClick={() => void refetch()}
                      className="underline hover:no-underline"
                    >
                      Reintentar
                    </button>
                  </AlertDescription>
                </Alert>
              </div>
            )}

            {!isLoading && !isError && groups.length === 0 && (
              <div className="flex flex-col items-center justify-center py-8 text-center text-sm text-muted-foreground px-4">
                <p>Aún no hay conversaciones. Empieza una nueva.</p>
              </div>
            )}

            {!isLoading &&
              !isError &&
              groups.map((group) => (
                <div key={group.label} className="mb-3">
                  <p className="mb-1 px-2 text-xs uppercase text-muted-foreground/60 tracking-wide font-medium">
                    {group.label}
                  </p>
                  <div className="space-y-0.5">
                    {group.items.map((conv) => (
                      <ConversationItem
                        key={conv.id}
                        conversation={conv}
                        isActive={conv.id === conversationId}
                        onSelect={handleSelect}
                      />
                    ))}
                  </div>
                </div>
              ))}
          </div>

          {/* Load more */}
          {hasNextPage && (
            <div className="pb-3 px-2">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => void fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Cargando..." : "Cargar 6 más"}
              </Button>
            </div>
          )}
        </ScrollArea>
      </div>
    );
  },
);
CopilotHistoryPanel.displayName = "CopilotHistoryPanel";
