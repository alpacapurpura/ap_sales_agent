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
  // When the user selects a conversation (history panel, rail avatar, etc.)
  // the store's conversationId changes. This effect fetches the detail and
  // replaces the store's messages once — not on every refetch — so that
  // locally-added messages in-flight between a send and server persistence
  // survive if a refetch lands first.
  const { data: detail } = useConversationDetail(conversationId);
  const hydratedIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!conversationId) {
      hydratedIdRef.current = null;
      return;
    }
    if (hydratedIdRef.current === conversationId) return;
    if (detail?.id !== conversationId) return;
    const currentCount = useCopilotStore.getState().messages.length;
    // Guard against a race where the user sends a message before the detail
    // request lands: if the store already holds more messages than the
    // server-side transcript, trust the local state.
    if (currentCount > detail.messages.length) {
      hydratedIdRef.current = conversationId;
      return;
    }
    const mapped = detail.messages
      .map(toCopilotMessage)
      .filter((m): m is CopilotMessage => m !== null);
    setMessages(mapped);
    hydratedIdRef.current = conversationId;
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
