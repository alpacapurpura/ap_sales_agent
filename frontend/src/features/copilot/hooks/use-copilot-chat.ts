"use client";

import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef } from "react";

import { streamCopilotChat, reportCopilotEvent } from "../api/copilot-api";
import { useCopilotStore, type UIAction, type AsyncJobState } from "../store/copilot-store";

import { handleUIAction } from "./use-copilot-ui-action";

import type { MessageBlock } from "../types/message-blocks";

/**
 * Unified chat hook — one POST /copilot/chat flow for every mode.
 *
 * Guided mode is driven entirely server-side: the backend reads the
 * conversation's ``procedure_state["guided"]`` flag and narrows tools +
 * system prompt accordingly. The frontend no longer sends mode hints.
 *
 * Single-flight guarantee: if a stream is already in progress when sendMessage
 * is called, the previous request is aborted BEFORE new messages are added to
 * the store. Streaming callbacks are bound to the specific assistant-message ID
 * created for this send, so late callbacks from aborted streams cannot write to
 * the wrong placeholder.
 */
export function useCopilotChat() {
  const conversationId = useCopilotStore((s) => s.conversationId);
  const currentRoute = useCopilotStore((s) => s.currentRoute);

  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  /** AbortController for the currently in-flight SSE request. */
  const abortRef = useRef<AbortController | null>(null);
  /**
   * ID of the assistant-message placeholder that the current stream writes to.
   * Stale callbacks from a previously aborted stream check this ref; if their
   * target ID no longer matches, they silently discard the update.
   */
  const activeAssistantIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, blocks?: MessageBlock[]) => {
      const trimmed = text.trim();
      const attachmentBlocks = blocks && blocks.length > 0 ? blocks : undefined;
      if (!trimmed && !attachmentBlocks) return;

      // ── Single-flight guard ──────────────────────────────────────────────
      // Abort BEFORE touching the store so stale callbacks fire on the OLD
      // activeAssistantIdRef value and self-discard (see guards in callbacks).
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const store = useCopilotStore.getState();

      // Open panel if not already
      store.openPanel();

      // Add user message — include blocks when present so UserMessageV2 renders attachments.
      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: trimmed,
        timestamp: Date.now(),
        blocks: attachmentBlocks,
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

      // Register the new placeholder as the active target AFTER adding it
      activeAssistantIdRef.current = assistantMsg.id;

      store.setStatus("thinking");

      // Capture the assistant ID for the closures below so they can self-check
      const myAssistantId = assistantMsg.id;

      try {
        const token = await getToken();
        if (!token) {
          if (activeAssistantIdRef.current === myAssistantId) {
            store.appendToLastAssistant(
              "\n\n_Error: No se pudo obtener el token de autenticación._",
            );
            store.setStatus("idle");
          }
          return;
        }

        const freshState = useCopilotStore.getState();
        const freshFields = freshState.selectedFields;
        const currentMessages = freshState.messages;

        // Derive guided flag from the active session for client-side telemetry;
        // the server authoritatively derives it from procedure_state.
        const mode = freshState.session?.procedure === "guided" ? "guided" : "chat";

        // Track message_sent event
        reportCopilotEvent(
          "message_sent",
          {
            message_length: text.trim().length,
            has_selected_fields: freshFields.length > 0,
            is_first_message: currentMessages.length <= 2,
            mode,
          },
          token,
        );

        /**
         * Guard: returns true only if this stream's placeholder is still the
         * active one. Stale callbacks from a previously aborted stream will
         * fail this check and silently discard their update.
         */
        const isActive = () => activeAssistantIdRef.current === myAssistantId;

        await streamCopilotChat(
          {
            message: trimmed,
            conversation_id: conversationId,
            blocks: attachmentBlocks as unknown as Record<string, unknown>[] | undefined,
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
            // SSE v2 (F8 §5.4) — block_delta is the canonical render path.
            // ``updateLastTextBlock`` appends to the last text block AND to
            // the legacy ``content`` field so the renderer keeps working
            // for both the new block-based renderer and any legacy reader.
            onBlockDelta: (data) => {
              if (!isActive()) return;
              const md = data.delta?.markdown;
              if (typeof md !== "string" || md.length === 0) return;
              useCopilotStore.getState().updateLastTextBlock(md);
            },
            onBlockAppend: (data) => {
              if (!isActive()) return;
              useCopilotStore
                .getState()
                .addBlockToLastAssistant(data.block as unknown as MessageBlock);
            },
            onStatus: (state) => {
              if (!isActive()) return;
              useCopilotStore
                .getState()
                .setStatus(state as "idle" | "thinking" | "streaming" | "done");
            },
            onDone: (convId) => {
              if (!isActive()) return;
              useCopilotStore.getState().setConversationId(convId);
              useCopilotStore.getState().setStatus("idle");
              // Keep the detail cache in sync so that selecting this
              // conversation from history later replays the fresh transcript.
              void queryClient.invalidateQueries({
                queryKey: ["copilot", "conversation", convId],
              });
              void queryClient.invalidateQueries({
                queryKey: ["copilot", "conversations"],
              });
            },
            onError: (message) => {
              if (!isActive()) return;
              // BE classifies the error and emits user-friendly Spanish-neutro
              // copy (see ``_user_facing_error_message`` in chat.py). It also
              // persists the same text as a tail AIMessage so the conversation
              // transcript shows it after a refresh. Render the message as-is
              // so live + refresh stay coherent — no ``_Error: ..._`` wrap.
              const store = useCopilotStore.getState();
              const last = store.messages[store.messages.length - 1];
              const prefix = last?.role === "assistant" && last.content ? "\n\n" : "";
              store.appendToLastAssistant(`${prefix}${message}`);
              store.setStatus("idle");
            },
            onToolStart: (tool) => {
              if (!isActive()) return;
              useCopilotStore.getState().addToolCallToLastAssistant(tool);
            },
            onToolResult: (tool, resultJson) => {
              if (!isActive()) return;

              // Parse job_id + poll_endpoint from tool result JSON
              let jobId: string | undefined;
              if (resultJson) {
                try {
                  const parsed = JSON.parse(resultJson) as Record<string, unknown>;
                  const rawJobId = parsed.job_id;
                  const rawPollEndpoint = parsed.poll_endpoint;
                  const rawModule = parsed.module;

                  if (
                    typeof rawJobId === "string" &&
                    typeof rawPollEndpoint === "string" &&
                    typeof rawModule === "string"
                  ) {
                    jobId = rawJobId;
                    const newJob: AsyncJobState = {
                      jobId: rawJobId,
                      module: rawModule as AsyncJobState["module"],
                      scope: (parsed.scope as AsyncJobState["scope"]) ?? "full",
                      mode: (parsed.mode as AsyncJobState["mode"]) ?? "initial",
                      section: (parsed.section as string) ?? null,
                      targetLabel: (parsed.target_label_es as string) ?? rawModule,
                      sourceKind: (parsed.source_kind as AsyncJobState["sourceKind"]) ?? "url",
                      sourceRef: (parsed.source_ref as string) ?? "",
                      pollEndpoint: rawPollEndpoint,
                      conversationId: useCopilotStore.getState().conversationId,
                      status: "queued",
                      progress: 0,
                      stage: "",
                      filledFields: [],
                      filledFieldsBySection: {},
                      sectionsTouched: [],
                      sectionsCompleted: [],
                      startedAt: Date.now(),
                    };
                    useCopilotStore.getState().registerJob(newJob);
                  }
                } catch {
                  // Malformed JSON — ignore, preserve existing behavior
                }
              }

              if (tool) {
                useCopilotStore.getState().markLastToolCallComplete(tool);

                if (jobId) {
                  // Patch jobId onto the matching tool call entry
                  const store = useCopilotStore.getState();
                  const msgs = store.messages;
                  const last = msgs[msgs.length - 1];
                  if (last?.role === "assistant" && last.toolCalls?.length) {
                    const tcs = [...last.toolCalls];
                    for (let i = tcs.length - 1; i >= 0; i--) {
                      if (tcs[i].tool === tool) {
                        tcs[i] = { ...tcs[i], jobId };
                        break;
                      }
                    }
                    store.setMessages(
                      msgs.map((m) => (m.id === last.id ? { ...last, toolCalls: tcs } : m)),
                    );
                  }
                }
              }
            },
            onUIAction: (action) => {
              if (!isActive()) return;
              handleUIAction(action as unknown as UIAction);
            },
          },
          token,
          controller.signal,
        );
      } catch (err) {
        if (
          (err as Error).name !== "AbortError" &&
          activeAssistantIdRef.current === myAssistantId
        ) {
          useCopilotStore
            .getState()
            .appendToLastAssistant("\n\n_Error de conexión. Intenta de nuevo._");
          useCopilotStore.getState().setStatus("idle");
        }
      }
    },
    [conversationId, currentRoute, getToken, queryClient],
  );

  const sendCardAction = useCallback(
    async (messageId: string, actionIndex: number, text: string) => {
      // V2 path (msg.blocks) keys by blockIndex; legacy (msg.uiActions) keys
      // by actionIndex. Both share the same numeric index from the renderer,
      // so resolve on both paths — whichever matches the message shape wins.
      const store = useCopilotStore.getState();
      store.updateUIActionStatus(messageId, actionIndex, "resolved");
      store.updateBlockCardStatus(messageId, actionIndex, "resolved");
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
