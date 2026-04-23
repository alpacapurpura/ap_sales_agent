"use client";

import { MoreHorizontal, PanelRightClose, Plus, Search, Target, Loader2 } from "lucide-react";
import { forwardRef, useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { useConversationGroups } from "../hooks/use-conversation-groups";
import { useConversationList } from "../hooks/use-conversation-list";
import { useCreateConversation } from "../hooks/use-create-conversation";
import { useDeleteConversation } from "../hooks/use-delete-conversation";
import { usePatchConversation } from "../hooks/use-patch-conversation";
import { useCopilotStore } from "../store/copilot-store";

import type { ConversationSummary } from "../types/conversations";

type CopilotHistoryPanelProps = React.HTMLAttributes<HTMLDivElement>;

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

// ── Conversation item ────────────────────────────────────────────────

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

  const progressPct =
    conversation.hasProcedure && conversation.procedureProgress !== null
      ? Math.round((conversation.procedureProgress ?? 0) * 100)
      : null;

  return (
    <div
      className={cn(
        "group relative cursor-pointer rounded-md px-2.5 py-2 transition-colors",
        isActive ? "bg-brand/10 ring-1 ring-inset ring-brand/30" : "hover:bg-muted/50",
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
      <div className="flex min-w-0 items-center gap-1.5">
        {conversation.hasProcedure && (
          <Target
            className={cn("h-3 w-3 shrink-0", isActive ? "text-brand" : "text-muted-foreground/60")}
            aria-hidden="true"
          />
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
            className="h-6 flex-1 px-1 py-0 text-xs"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span
            className={cn(
              "truncate text-[13px] text-foreground",
              isActive ? "font-semibold" : "text-foreground/90",
            )}
          >
            {title}
          </span>
        )}

        {!isEditing && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                onClick={(e) => e.stopPropagation()}
                aria-label="Opciones de conversación"
                className="ml-auto flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground opacity-0 transition hover:bg-muted group-hover:opacity-100"
              >
                <MoreHorizontal className="h-3.5 w-3.5" />
              </button>
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

      <div className="mt-0.5 flex items-center gap-1.5 text-[10.5px] text-muted-foreground">
        <span>{getRelativeTime(conversation.updatedAt)}</span>
        {progressPct !== null && (
          <span className="rounded bg-brand/20 px-1 font-medium text-brand">{progressPct}%</span>
        )}
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────

/**
 * History panel rendered in "full" sidebar state.
 * Lives at the right of the chat. Controls: hide-historial + new-conv + search + list.
 */
export const CopilotHistoryPanel = forwardRef<HTMLDivElement, CopilotHistoryPanelProps>(
  ({ className, ...props }, ref) => {
    const conversationId = useCopilotStore((s) => s.conversationId);
    const setConversationId = useCopilotStore((s) => s.setConversationId);
    const clearMessages = useCopilotStore((s) => s.clearMessages);
    const setStatus = useCopilotStore((s) => s.setStatus);
    const setSidebarState = useCopilotStore((s) => s.setSidebarState);

    const [searchQuery, setSearchQuery] = useState("");
    const loadMoreRef = useRef<HTMLDivElement>(null);

    const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage, refetch } =
      useConversationList({ limit: 6 });

    const { mutate: createConversation } = useCreateConversation();

    // Flatten + filter
    const allItems = data?.pages.flatMap((page) => page.items) ?? [];
    const filteredItems = searchQuery.trim()
      ? allItems.filter((c) =>
          (c.title ?? "").toLowerCase().includes(searchQuery.toLowerCase().trim()),
        )
      : allItems;
    const groups = useConversationGroups(filteredItems);

    // Infinite scroll — IntersectionObserver replaces "Cargar más" button
    useEffect(() => {
      const el = loadMoreRef.current;
      if (!el || !hasNextPage || isFetchingNextPage || searchQuery.trim()) return;
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting) void fetchNextPage();
        },
        { rootMargin: "200px" },
      );
      observer.observe(el);
      return () => observer.disconnect();
    }, [hasNextPage, isFetchingNextPage, fetchNextPage, searchQuery]);

    const handleSelect = (id: string) => {
      if (id === conversationId) return;
      setConversationId(id);
      clearMessages();
      setStatus("idle");
      setTimeout(() => document.getElementById("copilot-input")?.focus(), 50);
    };

    return (
      <TooltipProvider delayDuration={200}>
        <div
          ref={ref}
          className={cn(
            "flex h-full w-[280px] flex-col border-l border-border bg-background",
            className,
          )}
          {...props}
        >
          {/* Header */}
          <div className="flex h-12 items-center border-b border-border px-3">
            <h2 className="flex-1 text-sm font-semibold">Historial</h2>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={() => setSidebarState("rail")}
                  aria-label="Ocultar historial"
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
                >
                  <PanelRightClose className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Ocultar historial</TooltipContent>
            </Tooltip>
          </div>

          {/* Primary action */}
          <div className="p-2">
            <button
              type="button"
              onClick={() => createConversation()}
              className="group flex w-full items-center justify-between rounded-lg border border-brand/30 bg-brand/10 px-3 py-2 text-sm font-medium text-brand transition hover:border-brand/50 hover:bg-brand/15"
              aria-label="Nueva conversación"
            >
              <span className="inline-flex items-center gap-2">
                <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                Nueva conversación
              </span>
              <span className="rounded border border-brand/30 bg-background/50 px-1.5 py-0.5 font-mono text-[10px]">
                ⌘K
              </span>
            </button>
          </div>

          {/* Search */}
          <div className="px-2 pb-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar en historial…"
                className="h-8 border-border bg-background/50 pl-7 pr-2 text-xs"
                aria-label="Buscar conversaciones"
              />
            </div>
          </div>

          {/* List */}
          <ScrollArea className="flex-1">
            {isLoading && (
              <div className="space-y-2 px-2 py-2">
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
              <div className="flex flex-col items-center justify-center px-4 py-8 text-center text-sm text-muted-foreground">
                <p>
                  {searchQuery.trim()
                    ? "Sin resultados para tu búsqueda."
                    : "Aún no hay conversaciones. Empieza una nueva."}
                </p>
              </div>
            )}

            {!isLoading &&
              !isError &&
              groups.map((group) => (
                <div key={group.label}>
                  {/* Sticky group header — opaque bg, no border-b → keeps left panel border continuous */}
                  <div className="sticky top-0 z-10 bg-background px-3 pb-1 pt-3">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {group.label}
                    </span>
                  </div>
                  <div className="space-y-0.5 px-2 pb-1">
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

            {/* Infinite-scroll sentinel (disabled during active search) */}
            {hasNextPage && !searchQuery.trim() && (
              <div
                ref={loadMoreRef}
                className="flex items-center justify-center py-3 text-[10px] text-muted-foreground"
              >
                {isFetchingNextPage && (
                  <span className="inline-flex items-center gap-1.5">
                    <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                    Cargando más…
                  </span>
                )}
              </div>
            )}
          </ScrollArea>
        </div>
      </TooltipProvider>
    );
  },
);
CopilotHistoryPanel.displayName = "CopilotHistoryPanel";
