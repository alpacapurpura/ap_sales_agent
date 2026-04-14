"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Rocket } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { OfferArchetype } from "@/features/offer-studio/types";
import type { OfferFormValues } from "@/features/offer-studio/types/schema";
import { getEditionsCopy } from "@/features/offer-studio/utils/editions-copy";

interface EditionsOptInProps {
  archetype: OfferArchetype;
  currentValue: boolean | undefined;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
}

/**
 * Escape hatch for users who said "no editions" in the wizard but later want
 * to enable them (or vice versa). Rendered as a collapsible tucked at the
 * bottom of each archetype-specific details section. Closed by default — the
 * 99% of users who never change their mind won't even see it.
 *
 * Only renders for archetypes that support editions (PROGRAMA, SERVICIO,
 * EXPERIENCIA). PRODUCTO and MEMBRESIA never get one — their domain
 * validator forces has_editions=false regardless.
 */
export function EditionsOptIn({ archetype, currentValue, onSave }: EditionsOptInProps) {
  const copy = getEditionsCopy(archetype);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!copy) return null;

  // Default to true when the offer pre-dates this feature.
  const enabled = currentValue ?? true;

  const handleToggle = async () => {
    setSaving(true);
    try {
      await onSave({ has_editions: !enabled });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-8 pt-6 border-t border-dashed">
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            Opciones avanzadas
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-4">
          <div className="rounded-lg border bg-muted/20 p-4 space-y-3">
            <div className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                <Rocket className="h-4 w-4 text-primary" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  {enabled
                    ? "Esta oferta tiene ediciones activas"
                    : "¿Querés activar ediciones para esta oferta?"}
                </p>
                <p className="text-xs text-muted-foreground leading-snug">
                  {enabled
                    ? `Hoy podés gestionar ${copy.yesLabel.toLowerCase()}. Si la desactivás, la sección "Ediciones" se ocultará del editor.`
                    : copy.description}
                </p>
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                type="button"
                variant={enabled ? "outline" : "default"}
                size="sm"
                onClick={handleToggle}
                disabled={saving}
              >
                {saving ? "Guardando..." : enabled ? "Desactivar ediciones" : "Activar ediciones"}
              </Button>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
