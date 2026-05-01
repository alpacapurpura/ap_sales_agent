import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import type { LifecycleStage } from "../types";

interface LifecycleStageChipProps {
  stage: LifecycleStage;
  className?: string;
}

const STAGE_LABELS: Record<LifecycleStage, string> = {
  subscriber: "Suscriptor",
  lead: "Lead",
  mql: "MQL",
  sql: "SQL",
  opportunity: "Oportunidad",
  customer: "Cliente",
  evangelist: "Evangelista",
  churned: "Churn",
};

const STAGE_CLASSES: Record<LifecycleStage, string> = {
  subscriber: "bg-slate-100 text-slate-800 hover:bg-slate-100",
  lead: "bg-blue-100 text-blue-900 hover:bg-blue-100",
  mql: "bg-indigo-100 text-indigo-900 hover:bg-indigo-100",
  sql: "bg-violet-100 text-violet-900 hover:bg-violet-100",
  opportunity: "bg-amber-100 text-amber-900 hover:bg-amber-100",
  customer: "bg-green-100 text-green-900 hover:bg-green-100",
  evangelist: "bg-emerald-100 text-emerald-900 hover:bg-emerald-100",
  churned: "bg-red-100 text-red-800 hover:bg-red-100",
};

/**
 * Badge visual para la etapa de ciclo de vida de un contacto.
 * Colores basados en tokens Tailwind (no hex hardcodeado).
 */
export function LifecycleStageChip({ stage, className }: LifecycleStageChipProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(STAGE_CLASSES[stage], "border-0 font-medium", className)}
    >
      {STAGE_LABELS[stage]}
    </Badge>
  );
}
