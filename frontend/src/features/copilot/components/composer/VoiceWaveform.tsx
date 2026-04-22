"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

// Number of bars rendered. Higher = denser visual, more CPU per frame.
const BAR_COUNT = 40;
// Minimum bar height fraction (so silence still shows the baseline).
const MIN_SCALE = 0.08;
// Update throttle: push a new sample every ~50ms regardless of parent rerender rate.
const SAMPLE_INTERVAL_MS = 50;

interface VoiceWaveformProps {
  /** Normalized 0..1 live audio level from useVoiceRecorder. */
  level: number;
  /** Show static dotted baseline (used while transcribing). */
  dimmed?: boolean;
  className?: string;
}

/**
 * Rolling-history bar visualizer. Samples `level` on a fixed cadence and scrolls
 * the history left-to-right so the newest sample appears on the right edge.
 * Gracefully degrades to a flat baseline when the AudioContext failed.
 */
export function VoiceWaveform({ level, dimmed = false, className }: VoiceWaveformProps) {
  const [history, setHistory] = useState<number[]>(() => Array<number>(BAR_COUNT).fill(MIN_SCALE));
  const latestRef = useRef(level);

  useEffect(() => {
    latestRef.current = level;
  }, [level]);

  useEffect(() => {
    if (dimmed) return;
    const id = setInterval(() => {
      setHistory((prev) => {
        const next = prev.slice(1);
        // Apply a light curve so quiet speech is still visible.
        const shaped = Math.max(MIN_SCALE, Math.pow(latestRef.current, 0.6));
        next.push(shaped);
        return next;
      });
    }, SAMPLE_INTERVAL_MS);
    return () => clearInterval(id);
  }, [dimmed]);

  return (
    <div
      className={cn("flex h-6 flex-1 items-center gap-[2px] overflow-hidden", className)}
      aria-hidden="true"
    >
      {history.map((value, idx) => (
        <span
          key={idx}
          className={cn(
            "w-[2px] shrink-0 rounded-full transition-[height] duration-75 ease-out",
            dimmed ? "bg-muted-foreground/40" : "bg-foreground",
          )}
          style={{ height: `${Math.round(value * 100)}%` }}
        />
      ))}
    </div>
  );
}
