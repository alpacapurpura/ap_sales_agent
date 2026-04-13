"use client";

import { Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface VoiceButtonProps {
  isRecording: boolean;
  isTranscribing: boolean;
  disabled?: boolean;
  onMicClick: () => Promise<void>;
}

// ── Recording indicator ────────────────────────────────────────────────────

interface RecordingIndicatorProps {
  duration: number;
  onCancel: () => void;
  onStop: () => Promise<void>;
}

export function RecordingIndicator({
  duration,
  onCancel,
  onStop,
}: RecordingIndicatorProps) {
  return (
    <div className="flex flex-1 items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
      <div className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
      <span className="font-mono text-sm text-red-400">
        {formatDuration(duration)}
      </span>
      <span className="text-xs text-gray-400">Grabando...</span>
      <div className="ml-auto flex items-center gap-1.5">
        <button
          type="button"
          onClick={onCancel}
          aria-label="Cancelar grabación"
          className="flex h-7 w-7 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-white/10 hover:text-gray-200"
        >
          <Square className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={onStop}
          aria-label="Detener grabación"
          className="flex h-7 w-7 items-center justify-center rounded-md bg-red-500/20 text-red-400 transition-colors hover:bg-red-500/30"
        >
          <Square className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

// ── Transcribing indicator ─────────────────────────────────────────────────

export function TranscribingIndicator() {
  return (
    <div className="flex flex-1 items-center gap-2 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-2">
      <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
      <span className="text-sm text-purple-300">Transcribiendo...</span>
    </div>
  );
}

// ── Mic button ─────────────────────────────────────────────────────────────

export function VoiceButton({
  isRecording,
  isTranscribing,
  disabled = false,
  onMicClick,
}: VoiceButtonProps) {
  return (
    <button
      type="button"
      onClick={onMicClick}
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
  );
}
