"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronDown } from "lucide-react";
import { memo, useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useConversationDetail } from "../hooks/use-conversation-detail";
import { useCopilotChat } from "../hooks/use-copilot-chat";
import { useCopilotStore } from "../store/copilot-store";

import { ChatComposer } from "./composer/ChatComposer";
import { ContextRotBanner } from "./ContextRotBanner";
import { CopilotChatHeader } from "./CopilotChatHeader";
import { AssistantMessage } from "./messages/AssistantMessage";
import { AssistantMessageV2 } from "./messages/AssistantMessageV2";
import { TypingIndicator } from "./messages/TypingIndicator";
import { UserMessage } from "./messages/UserMessage";
import { UserMessageV2 } from "./messages/UserMessageV2";

import type { ReplyRef } from "./composer/ReplyPreview";
import type { CopilotMessage } from "../store/copilot-store";
import type { ConversationMessage } from "../types/conversations";
import type { MessageBlock } from "../types/message-blocks";

/**
 * Adapt a wire-level ConversationMessage into the store's CopilotMessage shape.
 * Tool-role messages are dropped — they belong to the LLM transcript, not the
 * rendered chat, which only renders user/assistant.
 */
function toCopilotMessage(msg: ConversationMessage): CopilotMessage | null {
  if (msg.role !== "user" && msg.role !== "assistant") return null;
  // Persisted messages are always "sent" or "error"; ephemeral statuses
  // ("sending"/"streaming") only exist mid-stream and never reach the wire.
  // The store's MessageStatus uses "thinking" instead of "sending"; since
  // hydrated messages can only be sent/error, we drop the field rather
  // than translate it to keep the contract explicit.
  const msgStatus = msg.status === "sent" || msg.status === "error" ? msg.status : undefined;
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: new Date(msg.createdAt).getTime(),
    blocks: (msg.blocks as MessageBlock[] | null) ?? undefined,
    msgStatus,
  };
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Full chat panel: header, message list, context rot banner, and composer.
 * Uses ChatComposer (V2) as input area with attachment and voice support.
 * Visible when sidebarState is "rail" or "full".
 */
export const CopilotChatPanel = memo(function CopilotChatPanel() {
  const messages = useCopilotStore((s) => s.messages);
  const status = useCopilotStore((s) => s.status);
  const conversationId = useCopilotStore((s) => s.conversationId);
  const setMessages = useCopilotStore((s) => s.setMessages);

  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [replyTo, setReplyTo] = useState<ReplyRef | null>(null);

  const { sendMessage, sendCardAction, stopStreaming } = useCopilotChat();

  // ── Hydration of historical conversations ─────────────────────────────
  //
  // Two distinct cases, one hook:
  //
  // 1. **First load of a conversation** — replace the store with the server
  //    transcript. This is the classic "user selected a conversation, show
  //    it" path.
  //
  // 2. **Mid-session refetch** (after `useAsyncToolJob.handleTerminal`
  //    invalidates the conversation query so the worker-emitted summary
  //    card + navigation pills appear) — MERGE by id. Keep existing local
  //    messages in-place (preserves ephemeral client-only fields like
  //    ``toolCalls`` that would otherwise be wiped because the server
  //    transcript doesn't carry them), append anything the server has that
  //    the store doesn't.
  //
  // A blind ``setMessages(serverMessages)`` on refetch wipes toolCalls from
  // the currently-streaming assistant message and the ToolCallChip vanishes.
  // We hit exactly that regression after Fix B — this merge-path undoes it.
  const { data: detail } = useConversationDetail(conversationId);
  const initialHydratedIdsRef = useRef<Set<string>>(new Set());
  const lastHydratedCountByIdRef = useRef<Record<string, number>>({});

  useEffect(() => {
    if (!conversationId) return;
    if (detail?.id !== conversationId) return;

    const serverCount = detail.messages.length;
    const lastHydratedCount = lastHydratedCountByIdRef.current[conversationId] ?? -1;
    if (lastHydratedCount === serverCount) return;

    const mapped = detail.messages
      .map(toCopilotMessage)
      .filter((m): m is CopilotMessage => m !== null);

    const store = useCopilotStore.getState();
    const currentMessages = store.messages;

    if (!initialHydratedIdsRef.current.has(conversationId)) {
      // First hydration for this conversation — replace is safe.
      if (currentMessages.length > serverCount) {
        // User started sending before detail landed. Preserve local state.
        lastHydratedCountByIdRef.current[conversationId] = serverCount;
        initialHydratedIdsRef.current.add(conversationId);
        return;
      }
      setMessages(mapped);
      initialHydratedIdsRef.current.add(conversationId);
      lastHydratedCountByIdRef.current[conversationId] = serverCount;
      return;
    }

    // Status-aware refetch strategy:
    //
    // - Mid-stream (``thinking``/``streaming``): merge by id so the currently
    //   streaming assistant placeholder keeps its ephemeral state (toolCalls,
    //   partial content). Server IDs differ from FE's ``crypto.randomUUID()``
    //   optimistic ids, so merge dedupes by id only — when ids don't match,
    //   merge keeps both and causes visible duplicates.
    // - Idle: stream completed. Server is authoritative for the whole turn
    //   (user msg + final assistant msg + any worker-emitted cards/pills).
    //   Full-replace by server transcript, discarding optimistic placeholders.
    //   This is the only moment where we can collapse the id mismatch without
    //   losing streaming state.
    const isMidStream = store.status === "thinking" || store.status === "streaming";
    if (!isMidStream) {
      setMessages(mapped);
      lastHydratedCountByIdRef.current[conversationId] = serverCount;
      return;
    }

    // Merge path — union by id. Keep local references where ids overlap so
    // ephemeral fields (toolCalls, msgStatus) survive the refetch.
    const localById = new Map(currentMessages.map((m) => [m.id, m]));
    const merged: CopilotMessage[] = mapped.map((serverMsg) => {
      const local = localById.get(serverMsg.id);
      if (!local) return serverMsg;
      return {
        ...local,
        content: serverMsg.content || local.content,
        blocks: serverMsg.blocks ?? local.blocks,
        msgStatus: serverMsg.msgStatus ?? local.msgStatus,
      };
    });

    const serverIds = new Set(mapped.map((m) => m.id));
    for (const local of currentMessages) {
      if (!serverIds.has(local.id)) merged.push(local);
    }

    setMessages(merged);
    lastHydratedCountByIdRef.current[conversationId] = serverCount;
  }, [conversationId, detail, setMessages]);

  const isLoading = status === "thinking" || status === "streaming";

  // Show typing indicator when no empty assistant placeholder exists
  const lastMsg = messages.length > 0 ? messages[messages.length - 1] : null;
  const showTypingIndicator =
    isLoading && !(lastMsg?.role === "assistant" && lastMsg?.content === "");

  // Virtualizer
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 80,
    overscan: 5,
    measureElement(element) {
      return element.getBoundingClientRect().height;
    },
  });

  // Smart auto-scroll: only scroll if autoScroll is active
  useEffect(() => {
    if (!autoScroll) return;
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length, showTypingIndicator, autoScroll]);

  // Detect manual scroll up → disable auto-scroll
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    // Within 60px of bottom = auto-scroll active
    setAutoScroll(distanceFromBottom < 60);
  }, []);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setAutoScroll(true);
    }
  }, []);

  const handleSend = useCallback(
    (text: string, blocks: MessageBlock[], reply?: ReplyRef) => {
      const composed = reply ? `[Respondiendo a: "${reply.preview}"]\n${text}` : text;
      const hasAttachments = blocks.some((b) => b.type !== "text" && b.type !== "quote_reply");

      if (!composed.trim() && !hasAttachments) return;
      void sendMessage(composed, blocks.length > 0 ? blocks : undefined);
      setReplyTo(null);
      setAutoScroll(true);
    },
    [sendMessage],
  );

  const handleReply = useCallback((message: CopilotMessage) => {
    const preview =
      message.blocks?.find((b) => b.type === "text")?.type === "text"
        ? ((
            message.blocks?.find((b) => b.type === "text") as
              | { type: "text"; markdown: string }
              | undefined
          )?.markdown?.slice(0, 80) ?? message.content.slice(0, 80))
        : message.content.slice(0, 80);

    setReplyTo({
      messageId: message.id,
      preview,
      role: message.role,
    });
  }, []);

  const handleClearReply = useCallback(() => {
    setReplyTo(null);
  }, []);

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  // Compute total tokens for rot banner (approximate from message count)
  const totalTokens = messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0);

  return (
    <div className="flex h-full flex-col border-l border-border bg-background">
      {/* Header */}
      <CopilotChatHeader />

      {/* Messages */}
      <div
        ref={scrollRef}
        data-testid="copilot-messages"
        // `min-h-0` lets `flex-1` actually shrink inside the parent flex column;
        // without it, tall content forces the track to grow and the composer
        // scrolls out of view.
        className="relative min-h-0 flex-1 overflow-y-auto px-4 py-4"
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-sm text-muted-foreground">
            <p className="font-medium">Escribe tu primera pregunta.</p>
          </div>
        ) : (
          <div style={{ height: `${totalSize}px`, position: "relative" }}>
            {virtualItems.map((virtualItem) => {
              const msg = messages[virtualItem.index];
              const isLastMsg = virtualItem.index === messages.length - 1;
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
                    msg.blocks ? (
                      <UserMessageV2 message={msg} onReply={handleReply} />
                    ) : (
                      <UserMessage message={msg} />
                    )
                  ) : msg.blocks ? (
                    <AssistantMessageV2
                      message={msg}
                      onReply={handleReply}
                      sendCardAction={sendCardAction}
                    />
                  ) : (
                    <AssistantMessage
                      message={msg}
                      isStreaming={isLoading && isLastMsg}
                      sendCardAction={sendCardAction}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {showTypingIndicator && (
          <div className="mt-2" aria-label="El copilot está escribiendo">
            <TypingIndicator />
          </div>
        )}

        {/* Stop streaming button */}
        {isLoading && (
          <div className="sticky bottom-2 flex justify-center">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={stopStreaming}
              className="h-7 gap-1 text-xs shadow-sm"
            >
              Detener
            </Button>
          </div>
        )}
      </div>

      {/* Scroll-to-bottom badge */}
      {!autoScroll && (
        <div className="absolute bottom-24 right-6 z-10">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={scrollToBottom}
            aria-label="Ir al final"
            className={cn("h-8 w-8 rounded-full p-0 shadow-md")}
          >
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      )}

      {/* Context rot banner */}
      {conversationId && (
        <ContextRotBanner
          conversationId={conversationId}
          totalTokens={totalTokens}
          messageCount={messages.length}
        />
      )}

      {/* Composer (V2) */}
      <ChatComposer
        onSend={handleSend}
        disabled={isLoading}
        replyTo={replyTo}
        onClearReply={handleClearReply}
      />
    </div>
  );
});
CopilotChatPanel.displayName = "CopilotChatPanel";
