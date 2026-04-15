"use client";

import { Send } from "lucide-react";
import { useRef, useState, useCallback } from "react";

import { cn } from "@/lib/utils";

import { useVoiceRecorder } from "../hooks/useVoiceRecorder";

import { AttachmentButton } from "./shared/attachment-button";
import { DocumentChip, type DocumentStatus } from "./shared/document-chip";
import { VoiceButton, RecordingIndicator, TranscribingIndicator } from "./shared/voice-button";

// ── Types ──────────────────────────────────────────────────────────────────

interface AttachedFile {
  file: File;
  status: DocumentStatus;
}

export interface CopilotInputProps {
  onSend: (text: string) => void;
  onFilesAttached?: (files: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

// ── Component ──────────────────────────────────────────────────────────────

export function CopilotInput({
  onSend,
  onFilesAttached,
  disabled = false,
  placeholder = "Escribe tu mensaje...",
}: CopilotInputProps) {
  const [value, setValue] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    isRecording,
    isTranscribing,
    startRecording,
    stopRecording,
    cancelRecording,
    error: voiceError,
    duration,
  } = useVoiceRecorder();

  const hasFiles = attachedFiles.length > 0;
  const isBusy = isRecording || isTranscribing;
  const canSend = (value.trim().length > 0 || hasFiles) && !disabled && !isBusy;

  // ── Handlers ────────────────────────────────────────────────────────────

  const handleSubmit = useCallback(() => {
    if (!canSend) return;

    if (hasFiles && onFilesAttached) {
      onFilesAttached(attachedFiles.map((af) => af.file));
    }

    if (value.trim().length > 0) {
      onSend(value.trim());
    } else if (hasFiles) {
      onSend("");
    }

    setValue("");
    setAttachedFiles([]);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [canSend, hasFiles, onFilesAttached, attachedFiles, value, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleMicClick = useCallback(async () => {
    if (isRecording) {
      const transcript = await stopRecording();
      if (transcript.trim()) {
        setValue(transcript.trim());
      }
    } else {
      await startRecording();
    }
  }, [isRecording, stopRecording, startRecording]);

  const handleFilesSelected = useCallback((files: File[]) => {
    const newAttached: AttachedFile[] = files.map((file) => ({
      file,
      status: "pending" as DocumentStatus,
    }));
    setAttachedFiles((prev) => [...prev, ...newAttached]);
  }, []);

  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="border-t border-white/10 bg-[#12122a] p-3">
      {voiceError && (
        <div
          role="alert"
          className="mb-2 rounded-md bg-red-500/10 px-3 py-1.5 text-xs text-red-400"
        >
          {voiceError}
        </div>
      )}

      {hasFiles && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {attachedFiles.map((af, index) => (
            <DocumentChip
              key={`${af.file.name}-${index}`}
              file={af.file}
              status={af.status}
              onRemove={() => handleRemoveFile(index)}
            />
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <AttachmentButton
          onFilesSelected={handleFilesSelected}
          disabled={disabled || isBusy}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-gray-400 hover:text-gray-200"
        />

        {isRecording ? (
          <RecordingIndicator
            duration={duration}
            onCancel={cancelRecording}
            onStop={handleMicClick}
          />
        ) : isTranscribing ? (
          <TranscribingIndicator />
        ) : (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
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
        )}

        <VoiceButton
          isRecording={isRecording}
          isTranscribing={isTranscribing}
          disabled={disabled}
          onMicClick={handleMicClick}
        />

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSend}
          aria-label="Enviar"
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
            canSend
              ? "bg-purple-600 text-white hover:bg-purple-700"
              : "cursor-not-allowed bg-white/5 text-gray-600 opacity-40",
          )}
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
