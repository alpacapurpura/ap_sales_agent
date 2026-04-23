"use client";

import { useMemo } from "react";

import { useDismissStore } from "../store/dismiss-store";

import type { Notification } from "../types";

/**
 * Aggregates user-facing notifications. The "paused interview" category was
 * retired with the standalone interview engine on 2026-04-22; a
 * guided-in-progress notification can be re-introduced later by querying
 * conversations whose ``procedure_state["guided"]`` is non-null.
 */
export function useNotifications(): {
  notifications: Notification[];
  dismiss: (id: string) => void;
} {
  const isDismissed = useDismissStore((s) => s.isDismissed);
  const dismiss = useDismissStore((s) => s.dismiss);

  const notifications = useMemo(() => {
    const all: Notification[] = [];
    return all.filter((n) => !isDismissed(n.id));
  }, [isDismissed]);

  return { notifications, dismiss };
}
