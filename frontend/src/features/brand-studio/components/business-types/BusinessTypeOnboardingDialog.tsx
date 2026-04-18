"use client";

import { Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";

import { BusinessTypeSelector } from "./BusinessTypeSelector";

import type { ExpertBusinessType } from "@/features/brand-studio/api/expert-business-types-api";

interface BusinessTypeOnboardingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called after successful save. */
  onComplete?: () => void;
}

/**
 * Full-screen onboarding dialog triggered on first Offer Studio visit when
 * the tenant has not yet declared their ``BrandIdentity.business_types``.
 *
 * Blocking-on-purpose: the selection drives format suitability scoring in
 * the Offer Studio wizard. An empty selection falls back to the full
 * catalog but the filtering is what makes the wizard feel "personalized",
 * so pushing the tenant to complete this once up-front is worth one
 * modal interaction.
 *
 * The selection can be revisited from Brand Studio settings (see
 * ``BusinessTypesSection``).
 */
export function BusinessTypeOnboardingDialog({
  open,
  onOpenChange,
  onComplete,
}: BusinessTypeOnboardingDialogProps) {
  const { settings, saving, updateIdentity } = useBrandSettings();
  const [selected, setSelected] = useState<ExpertBusinessType[]>(
    settings?.identity?.business_types ?? [],
  );

  const handleSave = async () => {
    if (!settings) return;
    await updateIdentity({
      ...(settings.identity ?? {}),
      business_types: selected,
    });
    onOpenChange(false);
    onComplete?.();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-5xl w-[95vw] max-h-[90vh] overflow-y-auto"
        // Block close-on-backdrop so the tenant explicitly commits.
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <DialogTitle className="text-2xl">¿Qué tipo de negocio manejas?</DialogTitle>
            </div>
            <DialogDescription className="text-base">
              Elegí uno o varios. Con esto podemos filtrar las ofertas que más encajan con tu
              negocio y ahorrarte ruido innecesario. Siempre podés cambiar esto después desde la
              configuración de tu marca.
            </DialogDescription>
          </div>

          <BusinessTypeSelector value={selected} onChange={setSelected} />

          <div className="flex items-center justify-between pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              {selected.length === 0
                ? "Seleccioná al menos una categoría. Si no encaja ninguna, podés dejarlo vacío y explorar todas."
                : `${selected.length} seleccionad${selected.length === 1 ? "a" : "as"}.`}
            </p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={saving}>
                Más tarde
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Guardar y continuar
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
