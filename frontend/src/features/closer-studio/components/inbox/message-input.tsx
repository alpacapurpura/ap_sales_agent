"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Send, Bot, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useConversationActions } from "../../hooks/use-conversation-actions";
import { useCloserStore } from "../../store/closer-store";
import type { HandlerMode, InputMode } from "../../types";

interface MessageInputProps {
  leadId: string;
  handlerMode: HandlerMode;
}

export function MessageInput({ leadId, handlerMode }: MessageInputProps) {
  const [text, setText] = useState("");
  const inputMode = useCloserStore((s) => s.inputMode);
  const setInputMode = useCloserStore((s) => s.setInputMode);
  const actions = useConversationActions(leadId);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed) return;

    actions.send.mutate(
      { content: trimmed, mode: inputMode },
      { onSuccess: () => setText("") },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDirect = inputMode === "direct";

  return (
    <div className="border-t bg-card p-3 shrink-0">
      {/* Mode toggle */}
      <div className="flex items-center gap-2 mb-2">
        <button
          onClick={() => setInputMode("direct")}
          className={cn(
            "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors",
            isDirect
              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
              : "text-muted-foreground hover:bg-muted",
          )}
        >
          <MessageSquare className="h-3 w-3" />
          Mensaje directo
        </button>
        <button
          onClick={() => setInputMode("instruction")}
          className={cn(
            "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors",
            !isDirect
              ? "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300"
              : "text-muted-foreground hover:bg-muted",
          )}
        >
          <Bot className="h-3 w-3" />
          Instruccion al AI
        </button>
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
              : "Instruccion para el AI (ej: 'Ofrece 10% descuento')"
          }
          className={cn(
            "flex-1 min-h-[40px] max-h-[120px] resize-none text-sm",
            !isDirect && "border-violet-300 focus-visible:ring-violet-400",
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
          La instruccion se inyectara en el proximo mensaje del AI. El lead no la vera.
        </p>
      )}
    </div>
  );
}
