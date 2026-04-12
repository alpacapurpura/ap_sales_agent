"use client";

import { useEffect, useRef } from "react";
import type { InterviewStatus } from "../../hooks/useInterviewChat";
import type { InterviewMessage as InterviewMessageType } from "../../hooks/useInterviewChat";
import { InterviewMessage } from "./interview-message";
import { InterviewInput } from "./interview-input";

interface InterviewChatPanelProps {
  messages: InterviewMessageType[];
  status: InterviewStatus;
  onSend: (text: string) => void;
  onCardAction: (text: string) => void;
}

export function InterviewChatPanel({
  messages,
  status,
  onSend,
  onCardAction,
}: InterviewChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === "thinking" || status === "streaming";

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex h-full flex-col bg-[#1a1a2e]">
      {/* Messages scroll area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-center text-sm text-gray-500">
            <div>
              <p className="font-medium text-gray-400">Iniciando entrevista...</p>
              <p className="mt-1 text-xs text-gray-600">
                Responde las preguntas para construir tu perfil de marca.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <InterviewMessage
            key={msg.id}
            message={msg}
            isStreaming={isStreaming && idx === messages.length - 1}
            onCardAction={onCardAction}
          />
        ))}
      </div>

      {/* Input */}
      <InterviewInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
