"use client";

import { memo, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
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
import { CopilotInput } from "./copilot-input";

export const CopilotChat = memo(function CopilotChat() {
  const messages = useCopilotStore((s) => s.messages);
  const status = useCopilotStore((s) => s.status);
  const activeProcedure = useCopilotStore((s) => s.activeProcedure);
  const isOpen = useCopilotStore((s) => s.isOpen);
  const clearActiveProcedure = useCopilotStore((s) => s.clearActiveProcedure);
  const { sendMessage, stopStreaming } = useCopilotChat();
  const { nudges, dismissNudge } = useProactiveNudges();
  const { getToken } = useAuth();
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevOpenRef = useRef(isOpen);

  const isLoading = status === "thinking" || status === "streaming";

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
        <CopilotInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="Escribe tu mensaje..."
        />
        {isLoading && (
          <button
            onClick={stopStreaming}
            className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
          >
            Detener
          </button>
        )}
      </div>
    </div>
  );
});
CopilotChat.displayName = "CopilotChat";
