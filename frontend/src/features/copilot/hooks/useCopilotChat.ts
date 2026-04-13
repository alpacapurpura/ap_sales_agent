"use client";

import { useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore, type UIAction } from "../store/copilot-store";
import { streamCopilotChat, reportCopilotEvent } from "../api/copilot-api";

/**
 * Unified chat hook for all copilot modes (chat, focus, interview).
 *
 * Mode is determined by the store state:
 * - interviewSessionId set → Interview mode
 * - focusEntity set → Focus mode
 * - Neither → Chat mode
 *
 * All messages go through POST /copilot/chat with mode context in the payload.
 */
export function useCopilotChat() {
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
        const token = await getToken();
        if (!token) {
          store.appendToLastAssistant("\n\n_Error: No se pudo obtener el token de autenticación._");
          store.setStatus("idle");
          return;
        }

        // Collect fresh field values from mounted WithCopilot components
        window.dispatchEvent(new CustomEvent("copilot:collect-values"));
        const freshState = useCopilotStore.getState();
        const freshFields = freshState.selectedFields;
        const currentMessages = freshState.messages;

        // Determine mode from store state
        const mode = freshState.interviewSessionId ? "interview"
          : freshState.focusEntity ? "focus" : "chat";

        // Track message_sent event
        reportCopilotEvent("message_sent", {
          message_length: text.trim().length,
          has_selected_fields: freshFields.length > 0,
          is_first_message: currentMessages.length <= 2,
          mode,
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
              focus: freshState.focusEntity ? {
                domain: freshState.focusEntity.domain,
                entity_id: freshState.focusEntity.entityId ?? null,
              } : null,
              interview_session_id: freshState.interviewSessionId ?? null,
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
              _handleUIAction(action as unknown as UIAction);
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

  const sendCardAction = useCallback(
    async (messageId: string, actionIndex: number, text: string) => {
      // Update card status to resolved before sending
      useCopilotStore.getState().updateUIActionStatus(messageId, actionIndex, "resolved");
      await sendMessage(text);
    },
    [sendMessage],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    useCopilotStore.getState().setStatus("idle");
  }, []);

  return { sendMessage, sendCardAction, stopStreaming };
}

/**
 * Route UIAction based on type.
 * Interview-specific actions get special handling.
 */
function _handleUIAction(action: UIAction): void {
  const store = useCopilotStore.getState();

  switch (action.type) {
    // Silent: update preview data, don't show as card
    case "preview_update":
      if (action.delta) {
        store.updatePreviewData(action.delta);
      }
      return;

    // Interview complete: attach card + clear interview state
    case "interview_complete":
      store.addUIActionToLastAssistant(action);
      store.clearInterview();
      return;

    // Navigation: attach card + enqueue for router
    case "navigate":
      store.addUIActionToLastAssistant(action);
      store.enqueuUIAction(action);
      return;

    // Procedure progress: update store for stepper
    case "procedure_progress":
      store.addUIActionToLastAssistant(action);
      if (action.procedure_id && action.steps) {
        store.setActiveProcedure({
          id: action.procedure_id,
          name: action.procedure_name || action.procedure_id,
          steps: action.steps,
          currentStepIndex: action.current_step_index ?? 0,
        });
      }
      return;

    // All other types (proposal, alternatives_card, clarify_card, checkpoint_card, etc.)
    default:
      store.addUIActionToLastAssistant(action);
      return;
  }
}
