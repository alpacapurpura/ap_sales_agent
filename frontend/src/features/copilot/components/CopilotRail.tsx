"use client";

import { ChevronLeft, ChevronRight, ChevronsRight, Plus } from "lucide-react";
import { forwardRef } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { useConversationList } from "../hooks/use-conversation-list";
import { useCreateConversation } from "../hooks/use-create-conversation";
import { useCopilotStore } from "../store/copilot-store";

// ── Types ────────────────────────────────────────────────────────────

type CopilotRailProps = React.HTMLAttributes<HTMLDivElement>;

// ── Helpers ──────────────────────────────────────────────────────────

function getInitials(title: string | null): string {
  if (!title) return "?";
  const words = title.trim().split(/\s+/);
  if (words.length === 1) return title.slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Always-visible 60px right-edge rail.
 * Contains: toggle button, separator, new conversation button,
 * and (when collapsed) up to 6 conversation avatars + "más" link.
 */
export const CopilotRail = forwardRef<HTMLDivElement, CopilotRailProps>(
  ({ className, ...props }, ref) => {
    const sidebarState = useCopilotStore((s) => s.sidebarState);
    const setSidebarState = useCopilotStore((s) => s.setSidebarState);
    const conversationId = useCopilotStore((s) => s.conversationId);

    const { mutate: createConversation } = useCreateConversation();
    const { data } = useConversationList({ limit: 6 });
    const topConversations = data?.pages[0]?.items.slice(0, 6) ?? [];

    // Rail is hidden in "full" state — controls migrate to CopilotHistoryPanel header.
    // Only show rail in "collapsed" and "rail" states.

    return (
      <TooltipProvider delayDuration={200}>
        <div
          ref={ref}
          className={cn(
            "flex flex-col items-center gap-2 w-[60px] border-l border-border bg-background px-2 py-3",
            className,
          )}
          {...props}
        >
          {/* State-specific toggle buttons */}
          {sidebarState === "collapsed" && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarState("rail")}
                  aria-label="Abrir chat"
                  className="h-9 w-9"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">Abrir chat</TooltipContent>
            </Tooltip>
          )}

          {sidebarState === "rail" && (
            <>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSidebarState("full")}
                    aria-label="Ver historial"
                    className="h-9 w-9"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left">Ver historial</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSidebarState("collapsed")}
                    aria-label="Cerrar chat"
                    className="h-9 w-9"
                  >
                    <ChevronsRight className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left">Cerrar chat</TooltipContent>
              </Tooltip>
            </>
          )}

          <Separator />

          {/* New conversation button — visible in collapsed and rail states */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => createConversation()}
                aria-label="Nueva conversación"
                className="h-9 w-9"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">Nueva conversación</TooltipContent>
          </Tooltip>

          {/* Avatars — only in collapsed state */}
          {sidebarState === "collapsed" && topConversations.length > 0 && (
            <div className="flex flex-col items-center gap-1.5 mt-1">
              {topConversations.map((conv) => {
                const isActive = conv.id === conversationId;
                return (
                  <Tooltip key={conv.id}>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => {
                          useCopilotStore.getState().setConversationId(conv.id);
                          setSidebarState("rail");
                        }}
                        aria-label={conv.title ?? "Conversación"}
                        className={cn(
                          "h-10 w-10 rounded-full flex items-center justify-center text-xs font-semibold",
                          "bg-muted text-muted-foreground transition-shadow",
                          isActive && "ring-2 ring-white ring-offset-1 ring-offset-accent",
                        )}
                        style={
                          isActive
                            ? { boxShadow: "0 0 0 2px white, 0 0 0 3.5px var(--color-accent)" }
                            : undefined
                        }
                      >
                        {getInitials(conv.title)}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      {conv.title ?? "Nueva conversación"}
                    </TooltipContent>
                  </Tooltip>
                );
              })}

              {/* "más" link */}
              <button
                type="button"
                onClick={() => setSidebarState("full")}
                aria-label="Ver todas las conversaciones"
                className="text-[10px] text-muted-foreground hover:text-foreground mt-0.5"
              >
                más
              </button>
            </div>
          )}
        </div>
      </TooltipProvider>
    );
  },
);
CopilotRail.displayName = "CopilotRail";
