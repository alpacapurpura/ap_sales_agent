"use client";

import { useRef, useState, useCallback } from "react";
import { Mic, MicOff, Send, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useVoiceRecorder } from "@/features/copilot/hooks/useVoiceRecorder";
import { AttachmentButton } from "@/features/copilot/components/shared/attachment-button";
import {
  DocumentChip,
  type DocumentStatus,
} from "@/features/copilot/components/shared/document-chip";

// ── Types ──────────────────────────────────────────────────────────────────

interface AttachedFile {
  file: File;
  status: DocumentStatus;
}

interface InterviewInputProps {
  onSend: (text: string) => void;
  onFilesAttached?: (files: File[]) => void;
  disabled?: boolean;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// ── Component ──────────────────────────────────────────────────────────────

export function InterviewInput({
  onSend,
  onFilesAttached,
  disabled = false,
}: InterviewInputProps) {
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
      // Send empty message to trigger processing when only files are attached
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
        onSend(transcript.trim());
      }
    } else {
      await startRecording();
    }
  }, [isRecording, stopRecording, startRecording, onSend]);

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
      {/* Voice error message */}
      {voiceError && (
        <div
          role="alert"
          className="mb-2 rounded-md bg-red-500/10 px-3 py-1.5 text-xs text-red-400"
        >
          {voiceError}
        </div>
      )}

      {/* Document chips */}
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
        {/* Attachment button */}
        <AttachmentButton
          onFilesSelected={handleFilesSelected}
          disabled={disabled || isBusy}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-gray-400 hover:text-gray-200"
        />

        {/* Text input or recording indicator */}
        {isRecording ? (
          <div className="flex flex-1 items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
            <span className="text-sm font-mono text-red-400">
              {formatDuration(duration)}
            </span>
            <span className="text-xs text-gray-400">Grabando...</span>
            <div className="ml-auto flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => cancelRecording()}
                aria-label="Cancelar grabación"
                className="flex h-7 w-7 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-white/10 hover:text-gray-200"
              >
                <MicOff className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={handleMicClick}
                aria-label="Detener grabación"
                className="flex h-7 w-7 items-center justify-center rounded-md bg-red-500/20 text-red-400 transition-colors hover:bg-red-500/30"
              >
                <Square className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ) : isTranscribing ? (
          <div className="flex flex-1 items-center gap-2 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-2">
            <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
            <span className="text-sm text-purple-300">Transcribiendo...</span>
          </div>
        ) : (
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
        )}

        {/* Mic button */}
        <button
          type="button"
          onClick={handleMicClick}
          disabled={disabled || isTranscribing}
          aria-label={isRecording ? "Detener grabación" : "Micrófono"}
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-colors",
            isRecording
              ? "border-red-500/50 bg-red-500/20 text-red-400 hover:bg-red-500/30"
              : "border-white/10 text-gray-400 hover:text-gray-200",
            (disabled || isTranscribing) && "cursor-not-allowed opacity-40",
          )}
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
