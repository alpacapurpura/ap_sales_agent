"use client";

import { Send, Bot, MessageSquare } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { useConversationActions } from "../../hooks/use-conversation-actions";

import type { HandlerMode, InputMode } from "../../types";

interface MessageInputProps {
  leadId: string;
  handlerMode: HandlerMode;
}

export function MessageInput({ leadId, handlerMode }: MessageInputProps) {
  const [text, setText] = useState("");
  const actions = useConversationActions(leadId);

  const effectiveMode: InputMode = handlerMode === "human" ? "direct" : "instruction";
  const isDirect = effectiveMode === "direct";

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed) return;

    actions.send.mutate(
      { content: trimmed, mode: effectiveMode },
      { onSuccess: () => setText("") },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-card p-3 shrink-0">
      {/* Mode label */}
      <div className="mb-2">
        {isDirect ? (
          <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
            <MessageSquare className="h-3 w-3" /> Mensaje directo al lead
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-violet-600 font-medium">
            <Bot className="h-3 w-3" /> Instrucción al AI
          </span>
        )}
      </div>

      {/* Input area */}
      <div className="flex gap-2 items-end">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isDirect
              ? "Escribe un mensaje al lead..."
              : "Instrucción para el AI (ej: 'Ofrece 10% descuento')"
          }
          className={cn(
            "flex-1 min-h-[40px] max-h-[120px] resize-none text-sm",
            isDirect
              ? "border-green-300 focus-visible:ring-green-400"
              : "border-violet-300 focus-visible:ring-violet-400",
          )}
          rows={1}
        />
        <Button
          size="icon"
          onClick={handleSend}
          disabled={!text.trim() || actions.send.isPending}
          className={cn(
            "shrink-0",
            isDirect ? "bg-green-600 hover:bg-green-700" : "bg-violet-600 hover:bg-violet-700",
          )}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      {/* Context hint */}
      {!isDirect && (
        <p className="text-[10px] text-violet-500 mt-1">
          La instrucción se inyectará en el próximo mensaje del AI. El lead no la verá.
        </p>
      )}
    </div>
  );
}
