"use client";

import { useState } from "react";

interface TabNotificationPermission {
  /** Request Notification permission if not yet decided. No-op if already granted/denied. */
  requestIfNeeded: () => Promise<void>;
  /** Returns true only when permission is "granted". */
  isGranted: () => boolean;
}

/**
 * Manages browser Notification permission state.
 * Requested on the first async job start so the user is not surprised.
 */
export function useTabNotificationPermission(): TabNotificationPermission {
  const [permission, setPermission] = useState<NotificationPermission>(() => {
    if (typeof Notification === "undefined") return "denied";
    return Notification.permission;
  });

  const requestIfNeeded = async (): Promise<void> => {
    if (typeof Notification === "undefined") return;
    if (permission !== "default") return;
    const result = await Notification.requestPermission();
    setPermission(result);
  };

  const isGranted = (): boolean => permission === "granted";

  return { requestIfNeeded, isGranted };
}
