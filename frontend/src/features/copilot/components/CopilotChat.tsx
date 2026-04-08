"use client";

import { memo, useEffect, useRef, useState } from "react";
import { Send, Square } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { useCopilotChat } from "../hooks/useCopilotChat";
import { useProactiveNudges } from "../hooks/useProactiveNudges";
import { reportCopilotEvent } from "../api/copilot-api";
import { UserMessage } from "./messages/UserMessage";
import { AssistantMessage } from "./messages/AssistantMessage";
import { SuggestedActions } from "./SuggestedActions";
import { ContextChips } from "./ContextChips";
import { ProcedureProgress } from "./ProcedureProgress";
import { NudgeBanner } from "./NudgeBanner";

export const CopilotChat = memo(function CopilotChat() {
  const messages = useCopilotStore((s) => s.messages);
  const status = useCopilotStore((s) => s.status);
  const activeProcedure = useCopilotStore((s) => s.activeProcedure);
  const isOpen = useCopilotStore((s) => s.isOpen);
  const clearActiveProcedure = useCopilotStore((s) => s.clearActiveProcedure);
  const { sendMessage, stopStreaming } = useCopilotChat();
  const { nudges, dismissNudge } = useProactiveNudges();
  const { getToken } = useAuth();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const prevOpenRef = useRef(isOpen);

  const isLoading = status === "thinking" || status === "streaming";

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Detect procedure_abandoned when panel closes mid-procedure
  useEffect(() => {
    if (prevOpenRef.current && !isOpen && activeProcedure) {
      const allCompleted = activeProcedure.steps.every((s) => s.status === "completed");
      if (!allCompleted) {
        getToken().then((token) => {
          if (token) {
            reportCopilotEvent("procedure_abandoned", {
              procedure_id: activeProcedure.id,
              procedure_name: activeProcedure.name,
              abandoned_at_step: activeProcedure.currentStepIndex,
              total_steps: activeProcedure.steps.length,
            }, token);
          }
        });
        clearActiveProcedure();
      }
    }
    prevOpenRef.current = isOpen;
  }, [isOpen, activeProcedure, getToken, clearActiveProcedure]);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Procedure stepper */}
      {activeProcedure && <ProcedureProgress />}

      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center text-sm text-slate-400">
            {/* Nudge banners when no messages */}
            {nudges.length > 0 ? (
              <div className="w-full space-y-2">
                {nudges.map((nudge) => (
                  <NudgeBanner
                    key={nudge.id}
                    nudge={nudge}
                    onAction={sendMessage}
                    onDismiss={dismissNudge}
                  />
                ))}
              </div>
            ) : (
              <>
                <p className="font-medium">Hola, soy tu Copilot</p>
                <p className="mt-1 text-xs">
                  Pregúntame sobre tu marca, ofertas, o cualquier cosa de tu negocio.
                </p>
              </>
            )}
          </div>
        )}

        {messages.map((msg, idx) =>
          msg.role === "user" ? (
            <UserMessage key={msg.id} message={msg} />
          ) : (
            <AssistantMessage
              key={msg.id}
              message={msg}
              isStreaming={isLoading && idx === messages.length - 1}
            />
          ),
        )}
      </div>

      {/* Suggested quick actions */}
      <SuggestedActions />

      {/* Context chips (selected fields) */}
      <ContextChips />

      {/* Input area */}
      <div className="border-t border-slate-200 p-3 dark:border-slate-700">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu mensaje..."
            rows={1}
            className="flex-1 resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition-colors placeholder:text-slate-400 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
            style={{ maxHeight: "120px" }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = "auto";
              target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
            }}
          />
          {isLoading ? (
            <Button
              size="icon"
              variant="ghost"
              onClick={stopStreaming}
              className="h-9 w-9 shrink-0 text-slate-500 hover:text-red-500"
            >
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="h-9 w-9 shrink-0 bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
});
CopilotChat.displayName = "CopilotChat";
