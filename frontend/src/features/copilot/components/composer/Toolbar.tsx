"use client";

import { Send } from "lucide-react";
import { forwardRef, useEffect, useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";

import { Button } from "@/components/ui/button";
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

    // Re-measure TextareaAutosize once the sidebar grid finishes its 220ms open
    // animation. Without this the textarea is measured at a narrow width and the
    // placeholder wraps into 5 rows until the user interacts.
    useEffect(() => {
      const id = window.setTimeout(() => {
        window.dispatchEvent(new Event("resize"));
      }, 260);
      return () => window.clearTimeout(id);
    }, []);

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

        {/* Textarea — auto-grows 1→5 rows then scrolls */}
        <TextareaAutosize
          ref={textareaRef}
          id="copilot-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe un mensaje..."
          minRows={1}
          maxRows={5}
          disabled={disabled || isRecording || isTranscribing}
          aria-label="Mensaje"
          className={cn(
            "flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm",
            "ring-offset-background placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
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
