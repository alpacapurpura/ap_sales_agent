"use client";

import { Mic, Square, X } from "lucide-react";
import { forwardRef } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────────────

interface VoiceOverlayProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Duration in seconds */
  duration: number;
  isTranscribing?: boolean;
  onCancel: () => void;
  onStop: () => void;
}

// ── Helpers ──────────────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Full-width overlay shown while audio is being recorded or transcribed.
 * Shows MM:SS timer, animated pulse, cancel and stop buttons.
 * Accessible: announces state changes via aria-live.
 */
export const VoiceOverlay = forwardRef<HTMLDivElement, VoiceOverlayProps>(
  ({ duration, isTranscribing = false, onCancel, onStop, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        role="region"
        aria-label="Grabación de voz activa"
        className={cn(
          "flex items-center gap-3 border-t border-border bg-background px-4 py-3",
          className,
        )}
        {...props}
      >
        {/* Live region for screen reader announcements */}
        <span role="status" aria-live="polite" className="sr-only">
          {isTranscribing ? "Transcribiendo audio..." : `Grabando: ${formatDuration(duration)}`}
        </span>

        {/* Pulse animation */}
        <span
          className="relative flex h-6 w-6 shrink-0 items-center justify-center"
          aria-hidden="true"
        >
          {!isTranscribing && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-60" />
          )}
          <span
            className={cn(
              "relative inline-flex h-4 w-4 rounded-full",
              isTranscribing ? "bg-purple-500 animate-pulse" : "bg-red-500",
            )}
          />
        </span>

        {/* Mic icon */}
        <Mic
          className={cn("h-4 w-4 shrink-0", isTranscribing ? "text-purple-500" : "text-red-500")}
          aria-hidden="true"
        />

        {/* Status text + timer */}
        <div className="flex flex-1 flex-col min-w-0">
          <span className="text-xs font-medium text-foreground">
            {isTranscribing ? "Transcribiendo..." : "Grabando"}
          </span>
          {!isTranscribing && (
            <span
              className="font-mono text-[10px] text-muted-foreground tabular-nums"
              aria-hidden="true"
            >
              {formatDuration(duration)}
            </span>
          )}
        </div>

        {/* Cancel button — discards recording */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onCancel}
          disabled={isTranscribing}
          aria-label="Cancelar grabación"
          className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </Button>

        {/* Stop button — transcribes + queues audio block */}
        <Button
          type="button"
          variant="destructive"
          size="icon"
          onClick={onStop}
          disabled={isTranscribing}
          aria-label="Detener grabación y transcribir"
          className="h-8 w-8 shrink-0"
        >
          <Square className="h-3.5 w-3.5" aria-hidden="true" />
        </Button>
      </div>
    );
  },
);
VoiceOverlay.displayName = "VoiceOverlay";
