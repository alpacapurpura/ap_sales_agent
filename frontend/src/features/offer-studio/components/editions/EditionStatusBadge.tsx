"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { EditionStatus } from "../../types";

const STATUS_CONFIG: Record<EditionStatus, { label: string; className: string }> = {
  [EditionStatus.DRAFT]: {
    label: "Borrador",
    className: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  },
  [EditionStatus.UPCOMING]: {
    label: "Próximo",
    className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  [EditionStatus.ACTIVE]: {
    label: "En Curso",
    className: "bg-green-500/10 text-green-500 border-green-500/20",
  },
  [EditionStatus.COMPLETED]: {
    label: "Completado",
    className: "bg-muted text-muted-foreground border-muted",
  },
  [EditionStatus.CANCELLED]: {
    label: "Cancelado",
    className: "bg-red-500/10 text-red-500 border-red-500/20",
  },
};

export function EditionStatusBadge({ status }: { status: EditionStatus }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG[EditionStatus.DRAFT];
  return (
    <Badge
      variant="outline"
      className={cn("text-[10px] font-semibold uppercase", config.className)}
    >
      {config.label}
    </Badge>
  );
}
