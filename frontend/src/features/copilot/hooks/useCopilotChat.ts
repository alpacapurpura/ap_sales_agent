"use client";

import { useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore, type UIAction } from "../store/copilot-store";
import { streamCopilotChat, reportCopilotEvent } from "../api/copilot-api";

export function useCopilotChat() {
  // Subscribe only to reactive values; read functions from getState() inside callbacks
  const conversationId = useCopilotStore((s) => s.conversationId);
  const currentRoute = useCopilotStore((s) => s.currentRoute);

  const { getToken } = useAuth();

  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const store = useCopilotStore.getState();

      // Open panel if not already
      store.openPanel();

      // Add user message
      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: text.trim(),
        timestamp: Date.now(),
      };
      store.addMessage(userMsg);

      // Create placeholder assistant message for streaming
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        content: "",
        timestamp: Date.now(),
      };
      store.addMessage(assistantMsg);

      // Abort any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      store.setStatus("thinking");

      try {
        // Get Clerk auth token
        const token = await getToken();
        if (!token) {
          store.appendToLastAssistant("\n\n_Error: No se pudo obtener el token de autenticación._");
          store.setStatus("idle");
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
              useCopilotStore.getState().appendToLastAssistant(content);
            },
            onStatus: (state) => {
              useCopilotStore.getState().setStatus(state as "idle" | "thinking" | "streaming" | "done");
            },
            onDone: (convId) => {
              useCopilotStore.getState().setConversationId(convId);
              useCopilotStore.getState().setStatus("idle");
            },
            onError: (message) => {
              useCopilotStore.getState().appendToLastAssistant(`\n\n_Error: ${message}_`);
              useCopilotStore.getState().setStatus("idle");
            },
            onToolStart: (tool) => {
              useCopilotStore.getState().appendToLastAssistant(`\n🔧 _${tool}..._\n`);
            },
            onToolResult: () => {
              // Tool result feeds back into the LLM via subsequent text_chunk
            },
            onUIAction: (action) => {
              const uiAction = action as unknown as UIAction;
              // Attach to the current assistant message for rendering NavigationCards
              useCopilotStore.getState().addUIActionToLastAssistant(uiAction);
              // Navigation actions execute immediately (reads, not writes)
              if (uiAction.type === "navigate") {
                useCopilotStore.getState().enqueuUIAction(uiAction);
              }
              // Procedure progress → update store for stepper
              if (uiAction.type === "procedure_progress" && uiAction.procedure_id && uiAction.steps) {
                useCopilotStore.getState().setActiveProcedure({
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
          useCopilotStore.getState().appendToLastAssistant("\n\n_Error de conexión. Intenta de nuevo._");
          useCopilotStore.getState().setStatus("idle");
        }
      }
    },
    [conversationId, currentRoute, getToken],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    useCopilotStore.getState().setStatus("idle");
  }, []);

  return { sendMessage, stopStreaming };
}
