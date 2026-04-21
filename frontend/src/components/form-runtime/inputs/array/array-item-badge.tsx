"use client";

import { cn } from "@/lib/utils";

export type ItemStatus = `complete` | `required-${string}`;

interface ArrayItemBadgeProps {
  status: ItemStatus;
  /** Label del campo faltante (extraído del status). Ej: "TÍTULO". */
  fieldLabel?: string;
}

/**
 * Badge de validación por ítem del array.
 *
 * Estados:
 * - complete           → verde/success — "COMPLETO"
 * - required-<field>   → rojo/destructive — "REQUIERE <FIELD>"
 */
export function ArrayItemBadge({ status, fieldLabel }: ArrayItemBadgeProps) {
  if (status === "complete") {
    return (
      <span
        className={cn(
          "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide",
          "border border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400",
        )}
      >
        Completo
      </span>
    );
  }

  if (status.startsWith("required-")) {
    const label = fieldLabel ?? status.replace("required-", "");
    return (
      <span
        className={cn(
          "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide",
          "border border-destructive/30 bg-destructive/10 text-destructive",
        )}
      >
        Requiere {label}
      </span>
    );
  }

  return null;
}

ArrayItemBadge.displayName = "ArrayItemBadge";
