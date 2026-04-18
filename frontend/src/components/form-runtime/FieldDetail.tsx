"use client";

import { ChevronLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { AutosaveBanner } from "./AutosaveBanner";
import { EditableField } from "./EditableField";
import { useFormRuntime } from "./FormRuntimeContext";

export interface FieldDetailProps {
  activeFieldId: string | null;
  onBack?: () => void;
  /** When true, render as a full-screen overlay (mobile <768px). */
  fullScreen?: boolean;
  className?: string;
}

/**
 * Right pane — renders the active field's input, autosave banner, and
 * description. On mobile this becomes a full-screen view with back button
 * (D13).
 */
export function FieldDetail({ activeFieldId, onBack, fullScreen, className }: FieldDetailProps) {
  const { schema, autosaveStatus, autosaveError } = useFormRuntime();
  const field = activeFieldId
    ? schema.fields.find((f) => f.id === activeFieldId)
    : schema.fields[0];

  return (
    <section
      className={cn(
        "flex min-h-full flex-col gap-4 p-4",
        fullScreen && "fixed inset-0 z-40 bg-background",
        className,
      )}
      aria-label={field?.label ?? "Detalle"}
    >
      {fullScreen && onBack && (
        <Button type="button" variant="ghost" size="sm" onClick={onBack} className="self-start">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Atrás
        </Button>
      )}

      {autosaveStatus && <AutosaveBanner status={autosaveStatus} error={autosaveError ?? null} />}

      {field ? (
        <EditableField field={field} autoFocus />
      ) : (
        <p className="text-sm text-muted-foreground">Seleccioná un campo</p>
      )}
    </section>
  );
}
