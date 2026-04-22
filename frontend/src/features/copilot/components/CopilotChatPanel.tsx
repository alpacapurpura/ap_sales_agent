"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import { memo, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { useCopilotChat } from "../hooks/use-copilot-chat";
import { useCopilotStore } from "../store/copilot-store";

import { ContextRotBanner } from "./ContextRotBanner";
import { CopilotChatHeader } from "./CopilotChatHeader";
import { AssistantMessage } from "./messages/AssistantMessage";
import { TypingIndicator } from "./messages/TypingIndicator";
import { UserMessage } from "./messages/UserMessage";
import { SlashCommandAutocomplete } from "./SlashCommandAutocomplete";

import type { SlashCommand } from "../types/conversations";

// ── Component ────────────────────────────────────────────────────────

/**
 * Full chat panel: header, message list, context rot banner, and input area.
 * Visible when sidebarState is "rail" or "full".
 */
export const CopilotChatPanel = memo(function CopilotChatPanel() {
  const messages = useCopilotStore((s) => s.messages);
  const status = useCopilotStore((s) => s.status);
  const conversationId = useCopilotStore((s) => s.conversationId);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const slashCommandOpen = useCopilotStore((s) => s.slashCommandOpen);
  const setSlashCommandOpen = useCopilotStore((s) => s.setSlashCommandOpen);

  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { sendMessage, sendCardAction } = useCopilotChat();

  const isLoading = status === "thinking" || status === "streaming";

  // Detect slash command trigger
  const slashQuery = inputValue.startsWith("/") ? inputValue.slice(1) : "";

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

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length, showTypingIndicator]);

  // Open slash autocomplete when input starts with "/"
  useEffect(() => {
    if (inputValue.startsWith("/") && !slashCommandOpen) {
      setSlashCommandOpen(true);
    } else if (!inputValue.startsWith("/") && slashCommandOpen) {
      setSlashCommandOpen(false);
    }
  }, [inputValue, slashCommandOpen, setSlashCommandOpen]);

  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;
    void sendMessage(trimmed);
    setInputValue("");
    setSlashCommandOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else if (e.key === "Escape") {
      setSidebarState("rail");
    }
  };

  const handleSlashSelect = (command: SlashCommand) => {
    setInputValue(`/${command.name} `);
    setSlashCommandOpen(false);
    textareaRef.current?.focus();
  };

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  // Compute total tokens for rot banner (approximate from message count)
  const totalTokens = useCopilotStore
    .getState()
    .messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0);

  return (
    <div className="flex h-full flex-col border-l border-border bg-background">
      {/* Header */}
      <CopilotChatHeader />

      {/* Messages */}
      <div
        ref={scrollRef}
        data-testid="copilot-messages"
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-sm text-muted-foreground">
            <p className="font-medium">Escribe tu primera pregunta.</p>
          </div>
        ) : (
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

        {showTypingIndicator && (
          <div className="mt-2" aria-label="El copilot está escribiendo">
            <TypingIndicator />
          </div>
        )}
      </div>

      {/* Context rot banner */}
      {conversationId && (
        <ContextRotBanner
          conversationId={conversationId}
          totalTokens={totalTokens}
          messageCount={messages.length}
        />
      )}

      {/* Input area */}
      <div className={cn("border-t border-border p-3")}>
        <SlashCommandAutocomplete
          query={slashQuery}
          onSelect={handleSlashSelect}
          onDismiss={() => setSlashCommandOpen(false)}
          open={slashCommandOpen && inputValue.startsWith("/")}
        >
          <div className="flex gap-2 items-end">
            <Textarea
              ref={textareaRef}
              id="copilot-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe un mensaje..."
              rows={1}
              disabled={isLoading}
              className="resize-none min-h-[36px] max-h-[120px] flex-1 text-sm"
            />
            <Button
              size="icon"
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
              aria-label="Enviar"
              className="h-9 w-9 shrink-0"
            >
              <span className="text-base leading-none">→</span>
            </Button>
          </div>
        </SlashCommandAutocomplete>
      </div>
    </div>
  );
});
CopilotChatPanel.displayName = "CopilotChatPanel";

// Prevent unused import lint for ScrollArea (imported for potential future use in inner scroll)
void ScrollArea;
