"use client";

import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type AutosaveStatus = "idle" | "saving" | "saved" | "error";

export interface AutosaveBannerProps {
  status: AutosaveStatus;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
}

const FADE_AFTER_MS = 2000;

function SavedBanner({ className }: { className?: string }) {
  const [faded, setFaded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setFaded(true), FADE_AFTER_MS);
    return () => clearTimeout(timer);
  }, []);

  if (faded) return null;
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md bg-green-50 px-3 py-2 text-xs text-green-700",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <CheckCircle2 className="h-3.5 w-3.5" />
      Guardado
    </div>
  );
}

/**
 * Inline banner shown at the top of the detail pane. Mirrors the autosave
 * hook state machine (idle → saving → saved | error). "Saved" fades after 2s
 * via the inner SavedBanner whose key resets the fade timer. D12 spec.
 */
export function AutosaveBanner({ status, error, onRetry, className }: AutosaveBannerProps) {
  if (status === "idle") return null;

  if (status === "saving") {
    return (
      <div
        className={cn(
          "flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground",
          className,
        )}
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Guardando…
      </div>
    );
  }

  if (status === "saved") {
    return <SavedBanner className={className} />;
  }

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive",
        className,
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="h-3.5 w-3.5" />
        <span>{error?.message ?? "Error al guardar"}</span>
      </div>
      {onRetry && (
        <Button type="button" size="sm" variant="outline" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </div>
  );
}
