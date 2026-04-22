"use client";

import { Send } from "lucide-react";
import { forwardRef, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { AttachmentButton } from "../shared/AttachmentButton";
import { VoiceButton } from "../shared/VoiceButton";

// ── Types ────────────────────────────────────────────────────────────

interface ToolbarProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onFilesSelected: (files: File[]) => void;
  onMicClick: () => Promise<void>;
  isRecording: boolean;
  isTranscribing: boolean;
  disabled?: boolean;
  /** Whether to accept images in attachment picker */
  acceptImages?: boolean;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Composer toolbar: [AttachmentButton][VoiceButton][TextArea autoresize][SendButton].
 * Keyboard: Enter=send, Shift+Enter=newline.
 */
export const Toolbar = forwardRef<HTMLDivElement, ToolbarProps>(
  (
    {
      value,
      onChange,
      onSend,
      onFilesSelected,
      onMicClick,
      isRecording,
      isTranscribing,
      disabled = false,
      acceptImages = true,
      className,
      ...props
    },
    ref,
  ) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    };

    const accept = acceptImages
      ? "image/*,.pdf,.docx,.txt,.md,.pptx,.mp3,.mp4,.webm,.ogg"
      : ".pdf,.docx,.txt,.md,.pptx";

    return (
      <div ref={ref} className={cn("flex items-end gap-1.5 px-3 py-2", className)} {...props}>
        {/* Attachment button */}
        <AttachmentButton
          onFilesSelected={onFilesSelected}
          disabled={disabled || isRecording || isTranscribing}
          accept={accept}
          className="h-8 w-8"
        />

        {/* Voice button */}
        <VoiceButton
          isRecording={isRecording}
          isTranscribing={isTranscribing}
          disabled={disabled}
          onMicClick={onMicClick}
        />

        {/* Textarea */}
        <Textarea
          ref={textareaRef}
          id="copilot-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe un mensaje..."
          rows={1}
          disabled={disabled || isRecording || isTranscribing}
          aria-label="Mensaje"
          className={cn(
            "flex-1 resize-none rounded-md text-sm",
            "min-h-[36px] max-h-[120px]",
            "overflow-y-auto",
          )}
        />

        {/* Send button */}
        <Button
          type="button"
          size="icon"
          onClick={onSend}
          disabled={disabled || !value.trim() || isRecording || isTranscribing}
          aria-label="Enviar mensaje"
          className="h-8 w-8 shrink-0"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    );
  },
);
Toolbar.displayName = "Toolbar";
