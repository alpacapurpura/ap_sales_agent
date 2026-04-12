"use client";

import { useCallback, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore } from "../store/copilot-store";
import { streamCopilotChat, getCopilotHeaders } from "../api/copilot-api";
import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

// ── Interview-specific UIAction types ──────────────────────────────────────

export type InterviewUIActionType =
  | "preview_update"
  | "alternatives_card"
  | "clarify_card"
  | "checkpoint_card"
  | "interview_complete";

export interface PreviewUpdateAction {
  type: "preview_update";
  delta: Record<string, unknown>;
}

export interface AlternativesCardAction {
  type: "alternatives_card";
  field_path: string;
  question: string;
  alternatives: Array<{
    id: string;
    title: string;
    description: string;
    recommended: boolean;
    recommendation_reason?: string;
  }>;
  allow_custom: boolean;
  status: "pending" | "resolved";
}

export interface ClarifyCardAction {
  type: "clarify_card";
  items: Array<{
    field_path: string;
    issue: string;
    options: string[];
  }>;
  status: "pending" | "resolved";
}

export interface CheckpointCardAction {
  type: "checkpoint_card";
  block_id: string;
  block_label: string;
  summary: Record<string, string>;
  health_score: number;
  blocks_progress: { completed: number; total: number };
  status: "pending" | "confirmed" | "revising";
}

export interface InterviewCompleteAction {
  type: "interview_complete";
  health_score: number;
  redirect: string;
}

export type InterviewUIAction =
  | PreviewUpdateAction
  | AlternativesCardAction
  | ClarifyCardAction
  | CheckpointCardAction
  | InterviewCompleteAction;

// ── Message type for the interview chat ────────────────────────────────────

export interface InterviewMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  uiActions?: InterviewUIAction[];
}

export type InterviewStatus = "idle" | "thinking" | "streaming" | "done";

// ── Hook ───────────────────────────────────────────────────────────────────

export function useInterviewChat(sessionId: string | null, conversationId: string | null) {
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [status, setStatus] = useState<InterviewStatus>("idle");

  const { getToken } = useAuth();
  const abortRef = useRef<AbortController | null>(null);

  // Add initial assistant message (e.g. from startInterview.initial_message)
  const addInitialMessage = useCallback((content: string) => {
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content,
      },
    ]);
  }, []);

  // Core send logic — used by both sendMessage and sendCardAction
  const send = useCallback(
    async (text: string, isCardAction: boolean = false) => {
      if (!text.trim()) return;

      // Add user message (card actions also show the user bubble)
      const userMsg: InterviewMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text.trim(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Add placeholder assistant message for streaming
      const assistantId = crypto.randomUUID();
      const assistantMsg: InterviewMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Abort any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setStatus("thinking");

      try {
        const token = await getToken();
        if (!token) {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === "assistant") {
              copy[copy.length - 1] = {
                ...last,
                content: "_Error: No se pudo obtener el token de autenticación._",
              };
            }
            return copy;
          });
          setStatus("idle");
          return;
        }

        // If we have an interview session, use the dedicated interview endpoint.
        // It accepts the same SSE format as the copilot chat endpoint.
        // Falls back to the general copilot chat with conversationId when no session.
        if (sessionId) {
          await streamInterviewMessage(
            sessionId,
            text.trim(),
            {
              onTextChunk: (chunk) => {
                setStatus("streaming");
                setMessages((prev) => {
                  const copy = [...prev];
                  const last = copy[copy.length - 1];
                  if (last && last.role === "assistant") {
                    copy[copy.length - 1] = {
                      ...last,
                      content: last.content + chunk,
                    };
                  }
                  return copy;
                });
              },
              onStatus: (state) => {
                setStatus(state as InterviewStatus);
              },
              onDone: (_convId) => {
                setStatus("idle");
              },
              onError: (message) => {
                setMessages((prev) => {
                  const copy = [...prev];
                  const last = copy[copy.length - 1];
                  if (last && last.role === "assistant") {
                    copy[copy.length - 1] = {
                      ...last,
                      content: `_Error: ${message}_`,
                    };
                  }
                  return copy;
                });
                setStatus("idle");
              },
              onUIAction: (action) => {
                const uiAction = action as unknown as InterviewUIAction;
                handleUIAction(uiAction, setMessages, setStatus);
              },
            },
            token,
            controller.signal,
          );
        } else {
          // Fallback: use the existing copilot chat SSE endpoint with conversation_id
          await streamCopilotChat(
            {
              message: text.trim(),
              conversation_id: conversationId,
              context: { locale: "es" },
            },
            {
              onTextChunk: (chunk) => {
                setStatus("streaming");
                setMessages((prev) => {
                  const copy = [...prev];
                  const last = copy[copy.length - 1];
                  if (last && last.role === "assistant") {
                    copy[copy.length - 1] = {
                      ...last,
                      content: last.content + chunk,
                    };
                  }
                  return copy;
                });
              },
              onStatus: (state) => {
                setStatus(state as InterviewStatus);
              },
              onDone: (_convId) => {
                setStatus("idle");
              },
              onError: (message) => {
                setMessages((prev) => {
                  const copy = [...prev];
                  const last = copy[copy.length - 1];
                  if (last && last.role === "assistant") {
                    copy[copy.length - 1] = {
                      ...last,
                      content: `_Error: ${message}_`,
                    };
                  }
                  return copy;
                });
                setStatus("idle");
              },
              onUIAction: (action) => {
                const uiAction = action as unknown as InterviewUIAction;
                handleUIAction(uiAction, setMessages, setStatus);
              },
            },
            token,
            controller.signal,
          );
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === "assistant") {
              copy[copy.length - 1] = {
                ...last,
                content: "_Error de conexión. Intenta de nuevo._",
              };
            }
            return copy;
          });
          setStatus("idle");
        }
      }

      void isCardAction; // used for semantic clarity only
    },
    [sessionId, conversationId, getToken],
  );

  /** Send a user-typed message */
  const sendMessage = useCallback(
    (text: string) => send(text, false),
    [send],
  );

  /** Send a card action on behalf of the user (auto-send) */
  const sendCardAction = useCallback(
    (text: string) => send(text, true),
    [send],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, []);

  return {
    messages,
    status,
    sendMessage,
    sendCardAction,
    stopStreaming,
    addInitialMessage,
  };
}

// ── UI Action handler ───────────────────────────────────────────────────────

function handleUIAction(
  uiAction: InterviewUIAction,
  setMessages: React.Dispatch<React.SetStateAction<InterviewMessage[]>>,
  _setStatus: React.Dispatch<React.SetStateAction<InterviewStatus>>,
) {
  if (uiAction.type === "preview_update") {
    // Silent update — no card rendered, just propagate to store
    useCopilotStore.getState().updateInterviewPreview(uiAction.delta);
    return;
  }

  if (uiAction.type === "interview_complete") {
    // Attach card to last assistant message; the card handles routing
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      if (last && last.role === "assistant") {
        const existing = last.uiActions ?? [];
        copy[copy.length - 1] = {
          ...last,
          uiActions: [...existing, uiAction],
        };
      }
      return copy;
    });
    // Clear interview state from store (routing is done by the card component)
    useCopilotStore.getState().clearInterview();
    return;
  }

  // All other card types: attach to the last assistant message
  setMessages((prev) => {
    const copy = [...prev];
    const last = copy[copy.length - 1];
    if (last && last.role === "assistant") {
      const existing = last.uiActions ?? [];
      copy[copy.length - 1] = {
        ...last,
        uiActions: [...existing, uiAction],
      };
    }
    return copy;
  });
}

// ── Interview-specific SSE streaming ───────────────────────────────────────

async function streamInterviewMessage(
  sessionId: string,
  message: string,
  callbacks: {
    onTextChunk: (content: string) => void;
    onStatus: (state: string) => void;
    onDone: (conversationId: string) => void;
    onError: (message: string) => void;
    onUIAction?: (action: Record<string, unknown>) => void;
  },
  token: string,
  signal?: AbortSignal,
): Promise<void> {
  const headers = getCopilotHeaders(token);
  headers["Content-Type"] = "application/json";

  const response = await fetch(
    `${API_URL}/api/v1/copilot/interview/${sessionId}/message`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ message }),
      signal,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    callbacks.onError(`Error ${response.status}: ${text}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No readable stream available");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      let currentEvent = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          const dataStr = line.slice(6);
          try {
            const data = JSON.parse(dataStr) as Record<string, unknown>;
            switch (currentEvent) {
              case "text_chunk":
                callbacks.onTextChunk(data.content as string);
                break;
              case "ui_action":
                callbacks.onUIAction?.(data);
                break;
              case "status":
                callbacks.onStatus(data.state as string);
                break;
              case "done":
                callbacks.onDone(data.conversation_id as string);
                break;
              case "error":
                callbacks.onError(data.message as string);
                break;
            }
          } catch {
            // Skip malformed JSON
          }
          currentEvent = "";
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
