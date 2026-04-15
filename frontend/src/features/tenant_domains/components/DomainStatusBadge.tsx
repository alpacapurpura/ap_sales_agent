"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import type { DomainStatus } from "../types";

interface StatusConfig {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  className?: string;
}

const STATUS_CONFIG: Record<DomainStatus, StatusConfig> = {
  active: { label: "Activo", variant: "default" },
  pending_verification: { label: "Pendiente", variant: "secondary" },
  verifying: {
    label: "Verificando",
    variant: "outline",
    className: "animate-pulse",
  },
  failed: { label: "Fallido", variant: "destructive" },
  suspended: { label: "Suspendido", variant: "destructive" },
};

interface DomainStatusBadgeProps {
  status: DomainStatus;
  className?: string;
}

export function DomainStatusBadge({ status, className }: DomainStatusBadgeProps) {
  const cfg = STATUS_CONFIG[status];
  return (
    <Badge variant={cfg.variant} className={cn(cfg.className, className)}>
      {cfg.label}
    </Badge>
  );
}
