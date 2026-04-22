"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { useCopilotStore } from "../../store/copilot-store";

interface ComposerContextChipsProps {
  className?: string;
}

/**
 * Context chips for selected fields — shown in the composer.
 * Shows max 3 chips + "+N más" expandable, plus "Limpiar" when > 1.
 */
export function ComposerContextChips({ className }: ComposerContextChipsProps) {
  const [expanded, setExpanded] = useState(false);
  const selectedFields = useCopilotStore((s) => s.selectedFields);
  const removeSelectedField = useCopilotStore((s) => s.removeSelectedField);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);

  if (selectedFields.length === 0) return null;

  const MAX_VISIBLE = 3;
  const visible = expanded ? selectedFields : selectedFields.slice(0, MAX_VISIBLE);
  const remaining = selectedFields.length - MAX_VISIBLE;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1.5 px-3 py-1.5 border-t border-border",
        className,
      )}
    >
      <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        Contexto
      </span>

      {visible.map((field) => (
        <Badge
          key={field.fieldId}
          variant="secondary"
          className="flex items-center gap-1 bg-purple-100 px-2 py-0.5 text-xs text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
        >
          <span>{field.fieldLabel}</span>
          <button
            type="button"
            onClick={() => removeSelectedField(field.fieldId)}
            aria-label={`Quitar contexto: ${field.fieldLabel}`}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                removeSelectedField(field.fieldId);
              }
            }}
            className="ml-0.5 rounded-full p-0.5 hover:bg-purple-200 dark:hover:bg-purple-800"
          >
            <X className="h-2.5 w-2.5" aria-hidden="true" />
          </button>
        </Badge>
      ))}

      {!expanded && remaining > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="text-xs text-muted-foreground hover:text-foreground"
          aria-label={`Ver ${remaining} campos más`}
        >
          +{remaining} más
        </button>
      )}

      {selectedFields.length > 1 && (
        <button
          type="button"
          onClick={clearSelectedFields}
          className="text-[10px] text-muted-foreground hover:text-foreground ml-auto"
        >
          Limpiar todo
        </button>
      )}
    </div>
  );
}

ComposerContextChips.displayName = "ComposerContextChips";
