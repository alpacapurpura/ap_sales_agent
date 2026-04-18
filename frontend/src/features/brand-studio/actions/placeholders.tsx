"use client";

import type { ActionComponent } from "@/lib/form-runtime/actions";

/**
 * Sprint 1 stubs for actions that port in Sprint 2. Each renders a visible
 * "pendiente" banner so schemas can reference them without crashing. The
 * stubs are replaced one-by-one in Sprint 2 via registerAction(..., { override: true }).
 */
function makePlaceholder(label: string): ActionComponent {
  function Placeholder() {
    return (
      <div className="rounded border border-dashed border-muted-foreground/40 bg-muted/40 p-3 text-xs text-muted-foreground">
        {label} — pendiente de portar en Sprint 2
      </div>
    );
  }
  Placeholder.displayName = `Placeholder(${label})`;
  return Placeholder;
}

export const VoiceClonePlaceholder = makePlaceholder("Clonación de voz");
export const PersonalityClonePlaceholder = makePlaceholder("Clonación de personalidad");
export const DimensionSlidersPlaceholder = makePlaceholder("Sliders de dimensiones");
export const PresetCatalogPlaceholder = makePlaceholder("Catálogo de presets");
export const BrandVisualsWizardPlaceholder = makePlaceholder("Wizard de visuales de marca");
export const SingleImagePickerPlaceholder = makePlaceholder("Selector de imagen");
export const ThemeInjectorPlaceholder = makePlaceholder("Inyector de tema");
export const LogoKitPlaceholder = makePlaceholder("Kit de logos");
export const ImageGalleryPickerPlaceholder = makePlaceholder("Galería de imágenes");
export const AvatarActionPlaceholder = makePlaceholder("Avatar");
export const SmartFillDialogPlaceholder = makePlaceholder("Auto-completar");
export const OnboardingWizardPlaceholder = makePlaceholder("Wizard de onboarding");
export const LegalActionPlaceholder = makePlaceholder("Datos legales");
