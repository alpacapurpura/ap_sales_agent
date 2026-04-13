"use client";

/**
 * @deprecated Use useCopilotChat instead. This wrapper exists for backward
 * compatibility with InterviewSplitView until Phase 3 replaces it.
 *
 * All interview chat now goes through the unified /copilot/chat endpoint
 * with interview_session_id in the context payload.
 */

import { useEffect, useCallback } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useCopilotChat } from "./useCopilotChat";

// Re-export interview-specific types for backward compatibility
export type InterviewUIActionType =
  | "preview_update"
  | "alternatives_card"
  | "clarify_card"
  | "checkpoint_card"
  | "interview_complete";

export type InterviewStatus = "idle" | "thinking" | "streaming";

export interface InterviewMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  uiActions?: InterviewUIAction[];
}

// ── Detailed card action types (kept for backward compatibility with consumers) ──

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

// ── Hook ────────────────────────────────────────────────────────────────────

export function useInterviewChat(
  sessionId: string | null,
  conversationId: string | null,
) {
  const { sendMessage: _send, stopStreaming } = useCopilotChat();

  // Sync sessionId into the store
  useEffect(() => {
    if (sessionId) {
      useCopilotStore.getState().setInterviewSession(sessionId);
    }
  }, [sessionId]);

  // Sync conversationId into the store
  useEffect(() => {
    if (conversationId) {
      useCopilotStore.getState().setConversationId(conversationId);
    }
  }, [conversationId]);

  // Map store messages to InterviewMessage shape
  const messages = useCopilotStore((s) =>
    s.messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      uiActions: m.uiActions as InterviewUIAction[] | undefined,
    })),
  );

  const status = useCopilotStore((s) => {
    if (s.status === "done") return "idle" as InterviewStatus;
    return s.status as InterviewStatus;
  });

  const sendMessage = useCallback(
    async (text: string) => {
      await _send(text);
    },
    [_send],
  );

  const sendCardAction = useCallback(
    async (text: string) => {
      await _send(text);
    },
    [_send],
  );

  const addInitialMessage = useCallback((content: string) => {
    useCopilotStore.getState().addMessage({
      id: crypto.randomUUID(),
      role: "assistant",
      content,
      timestamp: Date.now(),
    });
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
