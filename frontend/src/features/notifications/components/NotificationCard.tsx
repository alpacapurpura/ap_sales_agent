"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { Notification } from "../types";

interface NotificationCardProps {
  notification: Notification;
  onDismiss: (id: string) => void;
  onAction: () => void;
}

const SEVERITY_RING = {
  info: "border-l-purple-500",
  warning: "border-l-amber-500",
  success: "border-l-emerald-500",
} as const;

/**
 *
 */
export function NotificationCard({ notification, onDismiss, onAction }: NotificationCardProps) {
  return (
    <div
      className={cn(
        "group rounded-md border border-border bg-card/80 p-3 transition-colors hover:bg-card",
        "border-l-4",
        SEVERITY_RING[notification.severity],
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{notification.icon}</div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-foreground">{notification.title}</p>
          {notification.subtitle ? (
            <p className="mt-0.5 text-xs text-muted-foreground">{notification.subtitle}</p>
          ) : null}
          {notification.cta ? (
            <div className="mt-2">
              <Button
                size="sm"
                variant="secondary"
                className="h-7 text-xs"
                onClick={() => {
                  notification.cta?.onClick();
                  onAction();
                }}
              >
                {notification.cta.label}
              </Button>
            </div>
          ) : null}
        </div>
        {notification.dismissible ? (
          <button
            type="button"
            aria-label="Descartar"
            onClick={() => onDismiss(notification.id)}
            className="shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground group-hover:opacity-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
