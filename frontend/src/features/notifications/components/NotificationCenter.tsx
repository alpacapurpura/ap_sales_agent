"use client";

import { Bell } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

import { useNotifications } from "../hooks/use-notifications";

import { NotificationPanel } from "./NotificationPanel";

/**
 *
 */
export function NotificationCenter() {
  const { notifications, dismiss } = useNotifications();
  const [open, setOpen] = useState(false);

  if (notifications.length === 0 && !open) return null;

  const hasWarning = notifications.some((n) => n.severity === "warning");

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-40 flex flex-col items-end gap-2">
      <NotificationPanel
        open={open}
        notifications={notifications}
        onClose={() => setOpen(false)}
        onDismiss={dismiss}
      />
      {notifications.length > 0 ? (
        <button
          type="button"
          aria-label={`Avisos (${notifications.length})`}
          onClick={() => setOpen((v) => !v)}
          className={cn(
            "pointer-events-auto relative flex h-12 w-12 items-center justify-center rounded-full",
            "border border-border bg-card/95 shadow-lg backdrop-blur transition-transform",
            "hover:scale-105 active:scale-95",
          )}
        >
          <Bell className="h-5 w-5 text-foreground" />
          <span
            className={cn(
              "absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-bold text-white",
              hasWarning ? "bg-red-500" : "bg-purple-500",
            )}
          >
            {notifications.length}
          </span>
        </button>
      ) : null}
    </div>
  );
}
