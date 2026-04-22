"use client";

import { Check, Loader2, X } from "lucide-react";
import { forwardRef } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { VoiceWaveform } from "./VoiceWaveform";

// ── Types ────────────────────────────────────────────────────────────

interface VoiceOverlayProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Duration in seconds */
  duration: number;
  isTranscribing?: boolean;
  /** Normalized 0..1 live audio level */
  audioLevel?: number;
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
 * Overlay shown while audio is being recorded or transcribed.
 * Layout: [X cancel] [waveform reactive to mic] [timer] [✓ accept].
 * ChatGPT-style: red X destroys audio, green ✓ sends for transcription.
 */
export const VoiceOverlay = forwardRef<HTMLDivElement, VoiceOverlayProps>(
  (
    { duration, isTranscribing = false, audioLevel = 0, onCancel, onStop, className, ...props },
    ref,
  ) => {
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

        {/* Cancel button — discards recording, red accent */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onCancel}
          disabled={isTranscribing}
          aria-label="Descartar grabación"
          className={cn(
            "h-9 w-9 shrink-0 rounded-full border border-border",
            "text-destructive hover:bg-destructive/10 hover:text-destructive",
          )}
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </Button>

        {/* Waveform (reactive to mic input) */}
        <VoiceWaveform level={audioLevel} dimmed={isTranscribing} />

        {/* Timer */}
        <span
          className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums"
          aria-hidden="true"
        >
          {isTranscribing ? "…" : formatDuration(duration)}
        </span>

        {/* Accept button — stops + transcribes, green accent */}
        <Button
          type="button"
          size="icon"
          onClick={onStop}
          disabled={isTranscribing}
          aria-label="Aceptar y transcribir"
          className={cn(
            "h-9 w-9 shrink-0 rounded-full",
            "bg-emerald-600 text-white hover:bg-emerald-700",
            "focus-visible:ring-emerald-600",
          )}
        >
          {isTranscribing ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Check className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
      </div>
    );
  },
);
VoiceOverlay.displayName = "VoiceOverlay";
