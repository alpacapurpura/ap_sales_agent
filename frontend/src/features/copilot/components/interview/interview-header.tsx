"use client";

import { cn } from "@/lib/utils";

interface InterviewHeaderProps {
  currentBlockLabel: string;
  blocksCompleted: number;
  totalBlocks: number;
  /** Optional override for block display labels */
  blockLabels?: Record<string, string>;
  /** Title shown in the header (defaults to interview emoji + generic text) */
  title?: string;
}

/**
 * Header for the interview split view.
 * Shows the current block label and progress dots.
 * Generic — works for any interview domain.
 */
export function InterviewHeader({
  currentBlockLabel,
  blocksCompleted,
  totalBlocks,
  blockLabels,
  title = "Cocreando con tu consultor",
}: InterviewHeaderProps) {
  const label = blockLabels?.[currentBlockLabel] ?? currentBlockLabel;

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b bg-[#12122a] border-white/10">
      {/* Left: title + current block */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-white">{title}</span>
        {label && (
          <>
            <span className="text-white/30 text-sm">&middot;</span>
            <span className="text-sm text-purple-300 font-medium">
              {label}
            </span>
          </>
        )}
      </div>

      {/* Right: progress dots */}
      <div className="flex items-center gap-1.5">
        {Array.from({ length: totalBlocks }).map((_, idx) => {
          const isDone = idx < blocksCompleted;
          const isCurrent = idx === blocksCompleted;
          return (
            <span
              key={idx}
              className={cn(
                "inline-block rounded-full transition-all duration-300",
                isDone
                  ? "w-2 h-2 bg-emerald-400"
                  : isCurrent
                    ? "w-2.5 h-2.5 bg-purple-400 animate-pulse"
                    : "w-2 h-2 bg-white/20",
              )}
            />
          );
        })}
      </div>
    </div>
  );
}
