"use client";

import { useMemo } from "react";

import { useDismissStore } from "../store/dismiss-store";

import { useInterviewNotifications } from "./use-interview-notifications";

import type { Notification } from "../types";

/**
 *
 */
export function useNotifications(): {
  notifications: Notification[];
  dismiss: (id: string) => void;
} {
  const interview = useInterviewNotifications();
  const isDismissed = useDismissStore((s) => s.isDismissed);
  const dismiss = useDismissStore((s) => s.dismiss);

  const notifications = useMemo(() => {
    const all: Notification[] = [...interview];
    return all.filter((n) => !isDismissed(n.id));
  }, [interview, isDismissed]);

  return { notifications, dismiss };
}
