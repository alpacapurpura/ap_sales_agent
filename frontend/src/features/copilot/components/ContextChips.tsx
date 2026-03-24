"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useCopilotStore } from "../store/copilot-store";

/**
 * Shows selected field context chips above the chat input.
 * Each chip represents a field the user has added as context for the copilot.
 */
export function ContextChips() {
  const { selectedFields, removeSelectedField, clearSelectedFields } =
    useCopilotStore();

  if (selectedFields.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 border-t border-slate-200 px-3 pt-2 dark:border-slate-700">
      <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
        Contexto
      </span>
      {selectedFields.map((field) => (
        <Badge
          key={field.fieldId}
          variant="secondary"
          className="flex items-center gap-1 bg-purple-100 px-2 py-0.5 text-xs text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
        >
          {field.fieldLabel}
          <button
            type="button"
            onClick={() => removeSelectedField(field.fieldId)}
            className="ml-0.5 rounded-full p-0.5 hover:bg-purple-200 dark:hover:bg-purple-800"
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </Badge>
      ))}
      {selectedFields.length > 1 && (
        <button
          type="button"
          onClick={clearSelectedFields}
          className="text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          Limpiar
        </button>
      )}
    </div>
  );
}
