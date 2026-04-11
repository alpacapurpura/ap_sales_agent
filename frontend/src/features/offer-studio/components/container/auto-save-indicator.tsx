"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AutoSaveState } from "../../hooks/use-auto-save";

export interface AutoSaveIndicatorProps {
  state: AutoSaveState;
  lastSavedAt?: Date | null;
  errorMessage?: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Passive auto-save indicator with 4 visual states:
 *   idle    → hidden
 *   saving  → spinner + "Guardando..."
 *   saved   → check + "Guardado hace Ns"
 *   error   → alert icon + "Error al guardar" + retry button
 */
export function AutoSaveIndicator({
  state,
  lastSavedAt,
  errorMessage,
  onRetry,
  className,
}: AutoSaveIndicatorProps) {
  // Re-render every 10s so the "hace Ns" counter updates passively.
  const [, setTick] = useState(0);
  useEffect(() => {
    if (state !== "saved" || !lastSavedAt) return;
    const id = setInterval(() => setTick((t) => t + 1), 10_000);
    return () => clearInterval(id);
  }, [state, lastSavedAt]);

  if (state === "idle") return null;

  if (state === "saving") {
    return (
      <div
        className={cn(
          "flex items-center gap-1.5 text-xs text-muted-foreground",
          className,
        )}
        aria-live="polite"
      >
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
        <span>Guardando...</span>
      </div>
    );
  }

  if (state === "saved") {
    return (
      <div
        className={cn(
          "flex items-center gap-1.5 text-xs text-muted-foreground",
          className,
        )}
        aria-live="polite"
      >
        <Check className="h-3 w-3 text-emerald-500" aria-hidden />
        <span>
          Guardado
          {lastSavedAt ? ` hace ${formatSecondsAgo(lastSavedAt)}` : ""}
        </span>
      </div>
    );
  }

  // state === "error"
  return (
    <div
      className={cn(
        "flex items-center gap-2 text-xs text-destructive",
        className,
      )}
      role="alert"
    >
      <AlertCircle className="h-3 w-3" aria-hidden />
      <span>{errorMessage || "Error al guardar"}</span>
      {onRetry ? (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs text-destructive underline"
          onClick={onRetry}
        >
          Reintentar
        </Button>
      ) : null}
    </div>
  );
}

function formatSecondsAgo(date: Date): string {
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}
