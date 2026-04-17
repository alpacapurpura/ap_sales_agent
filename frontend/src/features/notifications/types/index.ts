import type { ReactNode } from "react";

export type NotificationType = "interview" | "connection" | "config" | "system";
export type NotificationSeverity = "info" | "warning" | "success";

export interface NotificationCTA {
  label: string;
  onClick: () => void;
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  subtitle?: string;
  icon: ReactNode;
  cta?: NotificationCTA;
  severity: NotificationSeverity;
  dismissible: boolean;
}
