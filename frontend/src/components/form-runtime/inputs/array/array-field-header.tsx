"use client";

import type React from "react";

import { cn } from "@/lib/utils";

interface ArrayFieldHeaderProps {
  /**
   * Optional. Normalmente el label del campo ya se renderiza en EditableField
   * (wrapper de form-runtime). Omitir para evitar duplicación. Pasar solo en
   * escenarios standalone (mockups, preview aislado).
   */
  title?: string;
  count: number;
  recommended?: number;
  onCollapseAll?: () => void;
  onExpandAll?: () => void;
  className?: string;
  /**
   * Optional slot for extra header actions (e.g. bulk-paste-AI CTA).
   * Rendered to the left of the collapse/expand buttons.
   */
  extraActions?: React.ReactNode;
}

/**
 * Header del container del array (Variante A).
 * Muestra contador + actions colapsar/expandir todo. El título del campo
 * se muestra arriba via EditableField — no duplicar aquí.
 */
export function ArrayFieldHeader({
  title,
  count,
  recommended,
  onCollapseAll,
  onExpandAll,
  className,
  extraActions,
}: ArrayFieldHeaderProps) {
  const counterLabel =
    recommended != null
      ? `${count} de ${recommended} recomendados`
      : `${count} ${count === 1 ? "ítem" : "ítems"}`;

  return (
    <div
      className={cn(
        "flex items-center justify-between px-5 py-3 border-b border-border bg-muted/30",
        className,
      )}
    >
      <div className="flex items-center gap-3">
        {title && <h3 className="font-semibold text-sm text-foreground">{title}</h3>}
        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
          {counterLabel}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {extraActions}

        {(onCollapseAll ?? onExpandAll) && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {onCollapseAll && (
              <button
                type="button"
                onClick={onCollapseAll}
                className="px-2 py-1 hover:text-foreground transition-colors"
              >
                Colapsar todo
              </button>
            )}
            {onCollapseAll && onExpandAll && <span className="text-muted-foreground/50">·</span>}
            {onExpandAll && (
              <button
                type="button"
                onClick={onExpandAll}
                className="px-2 py-1 hover:text-foreground transition-colors"
              >
                Expandir todo
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

ArrayFieldHeader.displayName = "ArrayFieldHeader";
