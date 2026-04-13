"use client";

import { Sparkles } from "lucide-react";

/**
 * Animated 3-dot typing indicator shown while the assistant is "thinking"
 * (after user sends a message, before the first streamed chunk arrives).
 */
export function TypingIndicator() {
  return (
    <div className="flex gap-2.5 px-4 py-1" data-testid="typing-indicator" aria-label="El asistente está escribiendo">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
        <Sparkles className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
      </div>
      <div className="flex items-center rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 dark:bg-slate-800">
        <span className="flex items-center gap-1">
          <span
            className="h-2 w-2 rounded-full bg-slate-400 animate-bounce dark:bg-slate-500"
            style={{ animationDelay: "0ms", animationDuration: "900ms" }}
          />
          <span
            className="h-2 w-2 rounded-full bg-slate-400 animate-bounce dark:bg-slate-500"
            style={{ animationDelay: "180ms", animationDuration: "900ms" }}
          />
          <span
            className="h-2 w-2 rounded-full bg-slate-400 animate-bounce dark:bg-slate-500"
            style={{ animationDelay: "360ms", animationDuration: "900ms" }}
          />
        </span>
      </div>
    </div>
  );
}
