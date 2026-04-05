"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Bot, Hand, Play, Square, User, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCloserStore } from "../../store/closer-store";
import { useConversationDetail } from "../../hooks/use-conversation-detail";
import { useConversationActions } from "../../hooks/use-conversation-actions";
import { MessageBubble } from "./message-bubble";
import { MessageInput } from "./message-input";

interface ConversationThreadProps {
  leadId: string;
}

export function ConversationThread({ leadId }: ConversationThreadProps) {
  const { data: detail, isLoading } = useConversationDetail(leadId);
  const actions = useConversationActions(leadId);
  const sidebarOpen = useCloserStore((s) => s.sidebarOpen);
  const setSidebarOpen = useCloserStore((s) => s.setSidebarOpen);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [detail?.messages]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Cargando conversacion...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Conversacion no encontrada
      </div>
    );
  }

  const isHuman = detail.handler_mode === "human";

  return (
    <div className="flex flex-col h-full">
      {/* Thread Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-card shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-semibold">
            {detail.display_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="text-sm font-semibold">{detail.display_name}</div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {isHuman ? (
                <span className="flex items-center gap-1 text-green-600">
                  <Square className="h-3 w-3 fill-current" /> Pausado por ti
                </span>
              ) : (
                <span className="flex items-center gap-1 text-violet-600">
                  <Bot className="h-3 w-3" /> AI Activo
                </span>
              )}
              {detail.channel && <span className="uppercase">{detail.channel}</span>}
              {detail.funnel_stage && (
                <span className="bg-muted px-1.5 py-0.5 rounded text-[10px]">
                  {detail.funnel_stage}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {isHuman ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => actions.resume.mutate(undefined)}
              disabled={actions.resume.isPending}
              className="text-violet-600 border-violet-200 hover:bg-violet-50"
            >
              <Play className="h-3.5 w-3.5 mr-1" />
              Reanudar AI
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => actions.stop.mutate()}
              disabled={actions.stop.isPending}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              <Hand className="h-3.5 w-3.5 mr-1" />
              STOP AI
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => actions.nudge.mutate(undefined)}
            disabled={actions.nudge.isPending}
            title="Nudge: AI envia mensaje proactivo"
          >
            <Zap className="h-3.5 w-3.5" />
          </Button>
          {!sidebarOpen && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSidebarOpen(true)}
              title="Ver perfil del contacto"
            >
              <User className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {detail.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* Input */}
      <MessageInput leadId={leadId} handlerMode={detail.handler_mode} />
    </div>
  );
}
