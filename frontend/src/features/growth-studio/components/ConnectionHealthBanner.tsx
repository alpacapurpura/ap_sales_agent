"use client";

import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { cn } from "@/lib/utils";

type HealthStatus = "healthy" | "expiring_soon" | "expired" | "not_connected";

interface ConnectionHealthBannerProps {
  status: HealthStatus;
  channelSlug: string;
  message: string;
  expiresAt?: string | null;
}

const STATUS_CONFIG: Record<
  Exclude<HealthStatus, "healthy">,
  {
    icon: typeof AlertCircle;
    containerClass: string;
    iconClass: string;
    linkLabel: string;
  }
> = {
  expiring_soon: {
    icon: AlertTriangle,
    containerClass: "border-amber-500/30 bg-amber-500/5 text-amber-700 dark:text-amber-400",
    iconClass: "text-amber-500",
    linkLabel: "Reconectar",
  },
  expired: {
    icon: AlertCircle,
    containerClass: "border-red-500/30 bg-red-500/5 text-red-700 dark:text-red-400",
    iconClass: "text-red-500",
    linkLabel: "Reconectar",
  },
  not_connected: {
    icon: Info,
    containerClass: "border-blue-500/30 bg-blue-500/5 text-blue-700 dark:text-blue-400",
    iconClass: "text-blue-500",
    linkLabel: "Conectar",
  },
};

export function ConnectionHealthBanner({
  status,
  channelSlug,
  message,
  expiresAt,
}: ConnectionHealthBannerProps) {
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;
  const connectionsHref = tenantId ? `/${tenantId}/connections` : "/connections";

  if (status === "healthy") return null;

  const cfg = STATUS_CONFIG[status];
  // Defense-in-depth: if the backend returns an unknown status (or mocks
  // provide undefined), degrade gracefully instead of crashing.
  if (!cfg) return null;
  const Icon = cfg.icon;

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border px-4 py-3 text-sm",
        cfg.containerClass,
      )}
      role="alert"
      data-channel={channelSlug}
      data-expires-at={expiresAt ?? undefined}
    >
      <Icon className={cn("h-4 w-4 shrink-0", cfg.iconClass)} />
      <p className="flex-1">{message}</p>
      <Link
        href={connectionsHref}
        className="shrink-0 text-xs font-medium underline underline-offset-2 hover:opacity-80"
      >
        {cfg.linkLabel}
      </Link>
    </div>
  );
}
