"use client";

import { useCallback, useRef } from "react";
import { useCopilotStore, type UIAction } from "../store/copilot-store";
import { streamCopilotChat } from "../api/copilot-api";

export function useCopilotChat() {
  const {
    conversationId,
    currentRoute,
    selectedFields,
    addMessage,
    appendToLastAssistant,
    addUIActionToLastAssistant,
    enqueuUIAction,
    setStatus,
    setConversationId,
    openPanel,
  } = useCopilotStore();

  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Open panel if not already
      openPanel();

      // Add user message
      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: text.trim(),
        timestamp: Date.now(),
      };
      addMessage(userMsg);

      // Create placeholder assistant message for streaming
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        content: "",
        timestamp: Date.now(),
      };
      addMessage(assistantMsg);

      // Abort any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setStatus("thinking");

      try {
        await streamCopilotChat(
          {
            message: text.trim(),
            conversation_id: conversationId,
            context: {
              current_route: currentRoute,
              selected_fields: selectedFields.map((f) => ({
                field_id: f.fieldId,
                field_label: f.fieldLabel,
                field_value: f.fieldValue,
              })),
              locale: "es",
            },
          },
          {
            onTextChunk: (content) => {
              appendToLastAssistant(content);
            },
            onStatus: (state) => {
              setStatus(state as "idle" | "thinking" | "streaming" | "done");
            },
            onDone: (convId) => {
              setConversationId(convId);
              setStatus("idle");
            },
            onError: (message) => {
              appendToLastAssistant(`\n\n_Error: ${message}_`);
              setStatus("idle");
            },
            onToolStart: (tool) => {
              appendToLastAssistant(`\n🔧 _${tool}..._\n`);
            },
            onToolResult: () => {
              // Tool result feeds back into the LLM via subsequent text_chunk
            },
            onUIAction: (action) => {
              const uiAction = action as unknown as UIAction;
              // Attach to the current assistant message for rendering NavigationCards
              addUIActionToLastAssistant(uiAction);
              // Navigation actions execute immediately (reads, not writes)
              if (uiAction.type === "navigate") {
                enqueuUIAction(uiAction);
              }
            },
          },
          controller.signal,
        );
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          appendToLastAssistant("\n\n_Error de conexión. Intenta de nuevo._");
          setStatus("idle");
        }
      }
    },
    [conversationId, currentRoute, selectedFields, addMessage, appendToLastAssistant, addUIActionToLastAssistant, enqueuUIAction, setStatus, setConversationId, openPanel],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, [setStatus]);

  return { sendMessage, stopStreaming };
}
