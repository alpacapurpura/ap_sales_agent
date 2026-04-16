"use client";

import { useAuth } from "@clerk/nextjs";
import { useVirtualizer } from "@tanstack/react-virtual";
import { memo, useEffect, useRef } from "react";

import { reportCopilotEvent } from "../api/copilot-api";
import { useCopilotChat } from "../hooks/use-copilot-chat";
import { useProactiveNudges } from "../hooks/use-proactive-nudges";
import { useCopilotStore } from "../store/copilot-store";

import { ContextChips } from "./ContextChips";
import { CopilotInput } from "./CopilotInput";
import { AssistantMessage } from "./messages/AssistantMessage";
import { TypingIndicator } from "./messages/TypingIndicator";
import { UserMessage } from "./messages/UserMessage";
import { NudgeBanner } from "./NudgeBanner";
import { ProcedureProgress } from "./ProcedureProgress";
import { SuggestedActions } from "./SuggestedActions";

export const CopilotChat = memo(function CopilotChat() {
  const messages = useCopilotStore((s) => s.messages);
  const status = useCopilotStore((s) => s.status);
  const activeProcedure = useCopilotStore((s) => s.activeProcedure);
  const isOpen = useCopilotStore((s) => s.isOpen);
  const clearActiveProcedure = useCopilotStore((s) => s.clearActiveProcedure);
  const { sendMessage, sendCardAction, stopStreaming } = useCopilotChat();
  const { nudges, dismissNudge } = useProactiveNudges();
  const { getToken } = useAuth();

  const scrollRef = useRef<HTMLDivElement>(null);
  const prevOpenRef = useRef(isOpen);

  const isLoading = status === "thinking" || status === "streaming";

  // AssistantMessage renders its own animated dots when content is empty.
  // Only show the external TypingIndicator when there is no empty assistant
  // placeholder already in the list — otherwise two indicators appear at once.
  const lastMsg = messages.length > 0 ? messages[messages.length - 1] : null;
  const showTypingIndicator =
    (status === "thinking" || status === "streaming") &&
    !(lastMsg?.role === "assistant" && lastMsg?.content === "");

  // Virtualizer — measures each item dynamically so variable-height messages work
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 80,
    overscan: 5,
    measureElement(element) {
      return element.getBoundingClientRect().height;
    },
  });

  // Auto-scroll to bottom on new messages or typing indicator change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length, showTypingIndicator]);

  // Detect procedure_abandoned when panel closes mid-procedure
  useEffect(() => {
    if (prevOpenRef.current && !isOpen && activeProcedure) {
      const allCompleted = activeProcedure.steps.every((s) => s.status === "completed");
      if (!allCompleted) {
        void getToken().then((token) => {
          if (token) {
            reportCopilotEvent(
              "procedure_abandoned",
              {
                procedure_id: activeProcedure.id,
                procedure_name: activeProcedure.name,
                abandoned_at_step: activeProcedure.currentStepIndex,
                total_steps: activeProcedure.steps.length,
              },
              token,
            );
          }
        });
        clearActiveProcedure();
      }
    }
    prevOpenRef.current = isOpen;
  }, [isOpen, activeProcedure, getToken, clearActiveProcedure]);

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  return (
    <div className="flex h-full flex-col">
      {/* Procedure stepper */}
      {activeProcedure && <ProcedureProgress />}

      {/* Messages area — virtualized */}
      <div
        ref={scrollRef}
        data-testid="copilot-messages"
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        {messages.length === 0 ? (
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
        ) : (
          /* Virtual scroll container — total height drives the scrollbar */
          <div style={{ height: `${totalSize}px`, position: "relative" }}>
            {virtualItems.map((virtualItem) => {
              const msg = messages[virtualItem.index];
              return (
                <div
                  key={virtualItem.key}
                  data-index={virtualItem.index}
                  ref={virtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    transform: `translateY(${virtualItem.start}px)`,
                    paddingBottom: "16px",
                  }}
                >
                  {msg.role === "user" ? (
                    <UserMessage message={msg} />
                  ) : (
                    <AssistantMessage
                      message={msg}
                      isStreaming={isLoading && virtualItem.index === messages.length - 1}
                      sendCardAction={sendCardAction}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Typing indicator rendered outside virtual list so it always sticks below */}
        {showTypingIndicator && (
          <div className="mt-2">
            <TypingIndicator />
          </div>
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
