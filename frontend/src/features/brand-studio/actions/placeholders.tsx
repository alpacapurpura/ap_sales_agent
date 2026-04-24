"use client";

import type { ActionComponent } from "@/lib/form-runtime/actions";

/**
 * Sprint 1 stubs for actions still pending port. Each renders a visible
 * "pendiente" banner so schemas can reference them without crashing.
 *
 * Sprint 2 replaces placeholders one-by-one (ported actions register in
 * registry.ts with { override: true }). The file shrinks as Sprint 2
 * progresses; Sprint 5 deletes it entirely once every action is live.
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

export const DimensionSlidersPlaceholder = makePlaceholder("Sliders de dimensiones");
export const BrandVisualsWizardPlaceholder = makePlaceholder("Wizard de visuales de marca");
export const LogoKitPlaceholder = makePlaceholder("Kit de logos");
export const ImageGalleryPickerPlaceholder = makePlaceholder("Galería de imágenes");
export const AvatarActionPlaceholder = makePlaceholder("Avatar");
