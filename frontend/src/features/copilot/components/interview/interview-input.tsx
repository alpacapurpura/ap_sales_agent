"use client";

import { useRef, useState } from "react";
import { Mic, Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface InterviewInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function InterviewInput({ onSend, disabled = false }: InterviewInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = value.trim().length > 0 && !disabled;

  const handleSubmit = () => {
    if (!canSend) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-white/10 bg-[#12122a] p-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe aquí..."
          rows={1}
          disabled={disabled}
          className={cn(
            "flex-1 resize-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none transition-colors",
            "placeholder:text-gray-500",
            "focus:border-purple-500 focus:ring-1 focus:ring-purple-500",
            disabled && "cursor-not-allowed opacity-50",
          )}
          style={{ maxHeight: "120px" }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = "auto";
            target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
          }}
          aria-label="Mensaje"
        />

        {/* Mic button — disabled until Phase 3 */}
        <button
          type="button"
          disabled
          title="Disponible en Fase 3"
          aria-label="Micrófono (disponible en Fase 3)"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-gray-600 cursor-not-allowed opacity-40"
        >
          <Mic className="h-4 w-4" />
        </button>

        {/* Send button */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSend}
          aria-label="Enviar"
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
            canSend
              ? "bg-purple-600 text-white hover:bg-purple-700"
              : "bg-white/5 text-gray-600 cursor-not-allowed opacity-40",
          )}
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
