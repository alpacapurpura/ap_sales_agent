"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface Alternative {
  id: string;
  title: string;
  description: string;
  recommended: boolean;
  recommendationReason?: string;
}

interface AlternativesCardProps {
  fieldPath: string;
  question: string;
  alternatives: Alternative[];
  allowCustom: boolean;
  onSelect: (alternativeId: string) => void;
  onCustom: () => void;
  status: "pending" | "resolved";
}

export function AlternativesCard({
  question,
  alternatives,
  allowCustom,
  onSelect,
  onCustom,
  status,
}: AlternativesCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const isResolved = status === "resolved";

  return (
    <div className="rounded-xl border border-purple-500 bg-[#1e1b4b] p-3.5">
      <div className="mb-2.5 flex items-center gap-1.5 text-xs font-semibold text-purple-300">
        <span>💡</span>
        <span>{question}</span>
      </div>

      <div className="space-y-1.5">
        {alternatives.map((alt) => (
          <button
            key={alt.id}
            disabled={isResolved}
            onClick={() => !isResolved && setSelected(alt.id)}
            className={cn(
              "w-full rounded-lg border bg-black/30 p-2.5 text-left transition-all",
              selected === alt.id
                ? "border-purple-400 bg-purple-500/15 ring-1 ring-purple-400"
                : "border-[#3d3d5c] hover:border-purple-400/50",
              isResolved && "cursor-default opacity-60"
            )}
          >
            <div className="text-xs font-semibold text-gray-200">{alt.title}</div>
            <div className="mt-0.5 text-[10px] text-gray-400">{alt.description}</div>
            {alt.recommended && alt.recommendationReason && (
              <div className="mt-1 text-[10px] text-purple-300">
                ✨ {alt.recommendationReason}
              </div>
            )}
          </button>
        ))}
      </div>

      <div className="mt-2.5 flex gap-2">
        <button
          disabled={!selected || isResolved}
          onClick={() => selected && onSelect(selected)}
          className="flex-1 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
          aria-label="Seleccionar"
        >
          Seleccionar
        </button>
        {allowCustom && (
          <button
            disabled={isResolved}
            onClick={onCustom}
            className="rounded-md border border-gray-600 px-3 py-1.5 text-xs text-gray-300 disabled:opacity-50"
          >
            Otro
          </button>
        )}
      </div>
    </div>
  );
}
