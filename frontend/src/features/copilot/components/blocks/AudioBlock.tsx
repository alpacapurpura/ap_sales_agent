"use client";

import { Mic, Pause, Play } from "lucide-react";
import { useRef, useState } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

import type { AudioBlock as AudioBlockType } from "../../types/message-blocks";

interface AudioBlockProps {
  block: AudioBlockType;
  className?: string;
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatCurrentTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * Custom audio player with play/pause, scrubber, speed control, and collapsible transcript.
 */
export function AudioBlock({ block, className }: AudioBlockProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(block.duration_ms ? block.duration_ms / 1000 : 0);
  const [speed, setSpeed] = useState<1 | 1.5 | 2>(1);
  const [transcriptOpen, setTranscriptOpen] = useState(false);

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      void audioRef.current.play();
    }
  };

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
      setCurrentTime(val);
    }
  };

  const cycleSpeed = () => {
    const next = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    setSpeed(next);
    if (audioRef.current) {
      audioRef.current.playbackRate = next;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!audioRef.current) return;
    if (e.key === " ") {
      e.preventDefault();
      handlePlayPause();
    } else if (e.key === "ArrowRight") {
      audioRef.current.currentTime = Math.min(duration, currentTime + 5);
    } else if (e.key === "ArrowLeft") {
      audioRef.current.currentTime = Math.max(0, currentTime - 5);
    }
  };

  const durationLabel = block.duration_ms ? formatTime(block.duration_ms) : "--:--";

  return (
    <div
      role="group"
      aria-label="Reproductor de audio"
      className={cn(
        "rounded-xl border border-border bg-muted/40 p-3 space-y-2 max-w-[320px]",
        className,
      )}
      onKeyDown={handleKeyDown}
    >
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={block.url}
        preload="metadata"
        onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime ?? 0)}
        onDurationChange={() => setDuration(audioRef.current?.duration ?? 0)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Header row */}
      <div className="flex items-center gap-2">
        <Mic className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
        <span className="text-xs font-medium text-foreground">Audio</span>
        <span className="ml-auto text-xs text-muted-foreground">{durationLabel}</span>
      </div>

      {/* Controls row */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handlePlayPause}
          aria-label={isPlaying ? "Pausar" : "Reproducir"}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-600 text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
        </button>

        {/* Scrubber */}
        <div className="flex flex-1 items-center gap-1.5">
          <input
            type="range"
            min={0}
            max={duration || 1}
            step={0.1}
            value={currentTime}
            onChange={handleScrub}
            aria-label="Progreso de audio"
            className="h-1 flex-1 appearance-none rounded bg-muted-foreground/30 accent-purple-600 cursor-pointer"
          />
          <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
            {formatCurrentTime(currentTime)} / {formatCurrentTime(duration)}
          </span>
        </div>

        {/* Speed */}
        <button
          type="button"
          onClick={cycleSpeed}
          aria-label={`Velocidad: ${speed}x`}
          className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          {speed}x
        </button>
      </div>

      {/* Transcript collapsible */}
      {block.transcript && (
        <Collapsible open={transcriptOpen} onOpenChange={setTranscriptOpen}>
          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="text-xs text-purple-600 hover:underline dark:text-purple-400"
            >
              {transcriptOpen ? "Ocultar transcripción" : "Ver transcripción"}
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <p className="mt-1.5 rounded-md bg-muted p-2 text-xs leading-relaxed text-muted-foreground">
              &ldquo;{block.transcript}&rdquo;
            </p>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}

AudioBlock.displayName = "AudioBlock";
