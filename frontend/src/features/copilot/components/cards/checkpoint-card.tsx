"use client";

import { memo } from "react";
import { cn } from "@/lib/utils";

interface CheckpointCardProps {
  blockId: string;
  blockLabel: string;
  summary: Record<string, string>;
  healthScore: number;
  blocksProgress: { completed: number; total: number };
  onConfirm: () => void;
  onRevise: () => void;
  status: "pending" | "confirmed" | "revising";
}

export const CheckpointCard = memo(function CheckpointCard({
  blockLabel,
  summary,
  healthScore,
  blocksProgress,
  onConfirm,
  onRevise,
  status,
}: CheckpointCardProps) {
  const isConfirmed = status === "confirmed";

  return (
    <div
      className={cn(
        "animate-in slide-in-from-bottom-2 fade-in duration-300 rounded-xl border p-3.5",
        isConfirmed
          ? "border-green-500 bg-green-900/20"
          : "border-purple-500 bg-[#1e1b4b]"
      )}
    >
      <div className="mb-2.5 flex items-center justify-between">
        <div className="text-xs font-semibold text-purple-300">
          {isConfirmed ? "✓" : "📋"} {blockLabel}
        </div>
        <div className="flex gap-1">
          {Array.from({ length: blocksProgress.total }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "h-2 w-2 rounded-full",
                i < blocksProgress.completed
                  ? "bg-green-500"
                  : i === blocksProgress.completed
                    ? "animate-pulse bg-purple-500"
                    : "bg-gray-600"
              )}
            />
          ))}
        </div>
      </div>

      <div className="mb-2.5 space-y-1 rounded-lg bg-black/30 p-2.5 text-xs leading-relaxed text-gray-200">
        {Object.entries(summary).map(([key, val]) => {
          const label = key.split(".").pop() ?? key;
          return (
            <div key={key}>
              <span className="font-semibold text-purple-300">{label}:</span>{" "}
              {val}
            </div>
          );
        })}
      </div>

      <div className="mb-2.5 rounded-md border border-green-500/30 bg-green-500/10 p-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-green-400">Health después de este bloque:</span>
          <span className="text-sm font-bold text-green-500">{healthScore}%</span>
        </div>
        <div className="mt-1.5 h-1 rounded-full bg-black/30">
          <div
            className="h-1 rounded-full bg-green-500"
            style={{ width: `${healthScore}%` }}
          />
        </div>
      </div>

      <div className="flex gap-2">
        <button
          disabled={isConfirmed}
          onClick={onConfirm}
          className="flex-1 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white transition-transform duration-150 active:scale-95 disabled:opacity-50"
          aria-label="Perfecto, sigamos"
        >
          👍 Perfecto, sigamos
        </button>
        <button
          disabled={isConfirmed}
          onClick={onRevise}
          className="rounded-md border border-gray-600 px-3 py-1.5 text-xs text-gray-300 transition-transform duration-150 active:scale-95 disabled:opacity-50"
          aria-label="Ajustar algo"
        >
          Ajustar algo
        </button>
      </div>
    </div>
  );
});
CheckpointCard.displayName = "CheckpointCard";
