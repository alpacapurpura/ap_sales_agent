"use client";

import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ArrayAddButtonProps {
  label: string;
  hint?: string;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Botón "Agregar {label}" con hint opcional de máximo recomendado.
 * Visible en el footer del container del array.
 */
export function ArrayAddButton({ label, hint, onClick, disabled, className }: ArrayAddButtonProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 py-3 border-t border-border",
        className,
      )}
    >
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={onClick}
        disabled={disabled}
        className="text-primary hover:text-primary/80 hover:bg-primary/5 gap-1.5 px-2"
      >
        <Plus className="h-4 w-4" />
        Agregar {label}
      </Button>
      {hint && <span className="text-[11px] text-muted-foreground">{hint}</span>}
    </div>
  );
}

ArrayAddButton.displayName = "ArrayAddButton";
