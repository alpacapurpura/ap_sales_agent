"use client";

import { useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore, type UIAction } from "../store/copilot-store";
import { streamCopilotChat, reportCopilotEvent } from "../api/copilot-api";

export function useCopilotChat() {
  const {
    conversationId,
    currentRoute,
    addMessage,
    appendToLastAssistant,
    addUIActionToLastAssistant,
    enqueuUIAction,
    setStatus,
    setConversationId,
    openPanel,
    setActiveProcedure,
  } = useCopilotStore();

  const { getToken } = useAuth();

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
        // Get Clerk auth token
        const token = await getToken();
        if (!token) {
          appendToLastAssistant("\n\n_Error: No se pudo obtener el token de autenticación._");
          setStatus("idle");
          return;
        }

        // Collect fresh field values from mounted WithCopilot components
        window.dispatchEvent(new CustomEvent("copilot:collect-values"));
        const freshFields = useCopilotStore.getState().selectedFields;
        const currentMessages = useCopilotStore.getState().messages;

        // Track message_sent event
        reportCopilotEvent("message_sent", {
          message_length: text.trim().length,
          has_selected_fields: freshFields.length > 0,
          is_first_message: currentMessages.length <= 2, // user + assistant placeholder
        }, token);

        await streamCopilotChat(
          {
            message: text.trim(),
            conversation_id: conversationId,
            context: {
              current_route: currentRoute,
              selected_fields: freshFields.map((f) => ({
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
              // Procedure progress → update store for stepper
              if (uiAction.type === "procedure_progress" && uiAction.procedure_id && uiAction.steps) {
                setActiveProcedure({
                  id: uiAction.procedure_id,
                  name: uiAction.procedure_name || uiAction.procedure_id,
                  steps: uiAction.steps,
                  currentStepIndex: uiAction.current_step_index ?? 0,
                });
              }
            },
          },
          token,
          controller.signal,
        );
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          appendToLastAssistant("\n\n_Error de conexión. Intenta de nuevo._");
          setStatus("idle");
        }
      }
    },
    [conversationId, currentRoute, getToken, addMessage, appendToLastAssistant, addUIActionToLastAssistant, enqueuUIAction, setStatus, setConversationId, openPanel, setActiveProcedure],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, [setStatus]);

  return { sendMessage, stopStreaming };
}
