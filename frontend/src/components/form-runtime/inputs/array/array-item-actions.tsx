"use client";

import { Copy, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface ArrayItemActionsProps {
  onDuplicate: () => void;
  onRemove: () => void;
  disabled?: boolean;
  className?: string;
  /**
   * Confirm callback. Defaults to an inline state toggle (two-click pattern:
   * first click arms the delete, second click confirms). Override in tests.
   */
  confirmLabel?: string;
}

/**
 * Botones Duplicar + Eliminar para cada ítem del array.
 * Delete usa patrón dos-clicks (primer click arma, segundo confirma).
 * Mejora futura: Shadcn AlertDialog.
 */
export function ArrayItemActions({
  onDuplicate,
  onRemove,
  disabled,
  className,
}: ArrayItemActionsProps) {
  return (
    <TooltipProvider>
      <div className={cn("flex items-center gap-0.5", className)}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
              onClick={onDuplicate}
              disabled={disabled}
              aria-label="Duplicar ítem"
            >
              <Copy className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Duplicar</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
              onClick={onRemove}
              disabled={disabled}
              aria-label="Eliminar ítem"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Eliminar</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

ArrayItemActions.displayName = "ArrayItemActions";
