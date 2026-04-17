"use client";

import { X } from "lucide-react";
import { useEffect } from "react";

import { cn } from "@/lib/utils";

import { NotificationCard } from "./NotificationCard";

import type { Notification } from "../types";

interface NotificationPanelProps {
  open: boolean;
  notifications: Notification[];
  onClose: () => void;
  onDismiss: (id: string) => void;
}

/**
 *
 */
export function NotificationPanel({
  open,
  notifications,
  onClose,
  onDismiss,
}: NotificationPanelProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <div
      role="dialog"
      aria-label="Centro de avisos"
      aria-live="polite"
      className={cn(
        "pointer-events-none absolute bottom-0 right-0 z-50 mb-2 w-[360px] origin-bottom-right",
        "transition-all duration-200 ease-out",
        open ? "pointer-events-auto translate-y-0 opacity-100" : "translate-y-2 opacity-0",
      )}
    >
      <div className="flex max-h-[60vh] flex-col overflow-hidden rounded-lg border border-border bg-popover shadow-xl">
        <header className="flex items-center justify-between border-b border-border px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">Avisos</span>
            {notifications.length > 0 ? (
              <span className="rounded-full bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                {notifications.length}
              </span>
            ) : null}
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="flex flex-col gap-2 overflow-y-auto p-3">
          {notifications.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Todo al día. Sin avisos pendientes.
            </p>
          ) : (
            notifications.map((n) => (
              <NotificationCard
                key={n.id}
                notification={n}
                onDismiss={onDismiss}
                onAction={onClose}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
