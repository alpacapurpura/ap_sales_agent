"use client";

import { memo } from "react";

interface ClarifyItem {
  fieldPath: string;
  issue: string;
  options: string[];
}

interface ClarifyCardProps {
  items: ClarifyItem[];
  onResolve: (resolution: string) => void;
  status: "pending" | "resolved";
}

/** Must mirror MAX_CLARIFY_ITEMS in backend shared_tools/clarify.py. */
const MAX_CLARIFY_ITEMS = 4;

export const ClarifyCard = memo(function ClarifyCard({
  items,
  onResolve,
  status,
}: ClarifyCardProps) {
  const isResolved = status === "resolved";

  if (isResolved) {
    return (
      <div className="animate-in slide-in-from-bottom-2 fade-in duration-300 rounded-xl border border-green-500/50 bg-green-900/20 px-3.5 py-2 text-xs text-green-400">
        ✓ Aclarado
      </div>
    );
  }

  return (
    <div className="animate-in slide-in-from-bottom-2 fade-in duration-300 rounded-xl border border-amber-500 bg-[#422006] p-3.5">
      <div className="mb-2.5 flex items-center gap-1.5 text-xs font-semibold text-amber-400">
        <span>⚠️</span>
        <span>Algo no cuadra</span>
      </div>

      {items.slice(0, MAX_CLARIFY_ITEMS).map((item, idx) => (
        <div key={idx} className="mb-2 rounded-lg bg-black/30 p-2.5">
          <div className="text-xs text-gray-200">{item.issue}</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {item.options.map((opt, optIdx) => (
              <button
                key={optIdx}
                onClick={() => onResolve(opt)}
                className="rounded-md border border-gray-600 px-2.5 py-1 text-[10px] text-gray-300 transition-transform duration-150 active:scale-95 hover:border-amber-400 hover:text-amber-300"
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
});
ClarifyCard.displayName = "ClarifyCard";
