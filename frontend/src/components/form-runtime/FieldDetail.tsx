"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { AutosaveBanner } from "./AutosaveBanner";
import { EditableField } from "./EditableField";
import { useFormRuntime } from "./FormRuntimeContext";

export interface FieldDetailProps {
  activeFieldId: string | null;
  /** Href to return to (used by the mobile back button). */
  backHref?: string;
  /** When true, render as a full-screen overlay (mobile <768px). */
  fullScreen?: boolean;
  className?: string;
}

/**
 * Right pane — renders the active field's input, autosave banner and label.
 * On mobile (<768px) the pane becomes a full-screen overlay; the back
 * affordance is a Next.js Link so navigation lives in the URL.
 */
export function FieldDetail({ activeFieldId, backHref, fullScreen, className }: FieldDetailProps) {
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
      {fullScreen && backHref && (
        <Button type="button" variant="ghost" size="sm" asChild className="self-start">
          <Link href={backHref}>
            <ChevronLeft className="mr-1 h-4 w-4" />
            Atrás
          </Link>
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
