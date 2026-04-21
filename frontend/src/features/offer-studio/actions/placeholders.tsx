"use client";

/**
 * Placeholder action components.
 *
 * Each ``custom`` field in an offer-studio schema references an action key
 * (see ``hint`` attrs in ``schemas/*.schema.ts``). The registry points each
 * key at a placeholder or a real ported action — Sprint 15+ progressively
 * replaces placeholders with real implementations.
 *
 * Until then, each placeholder renders a muted "pendiente" card so the
 * editor is inspectable end-to-end without crashing when a schema mounts
 * a not-yet-ported action. Matches the pattern from brand-studio.
 */

import type { ReactElement } from "react";

interface PlaceholderProps {
  label: string;
  actionKey: string;
}

function ActionPlaceholder({ label, actionKey }: PlaceholderProps): ReactElement {
  return (
    <div className="rounded-md border border-dashed border-muted-foreground/30 bg-muted/20 p-4 text-sm text-muted-foreground">
      <p className="font-medium text-foreground">{label}</p>
      <p className="mt-1">
        Acción <code className="rounded bg-muted px-1 py-0.5 text-xs">{actionKey}</code> pendiente
        de portar.
      </p>
    </div>
  );
}

/** Create a bound placeholder so consumers mount a ready-to-render component. */
function createPlaceholderAction(actionKey: string, label: string) {
  return function Placeholder(): ReactElement {
    return <ActionPlaceholder label={label} actionKey={actionKey} />;
  };
}

// ─── Named placeholders (exported individually so registry imports stay explicit) ──

export const PricingOptionsBuilderPlaceholder = createPlaceholderAction(
  "offer-pricing-options-builder",
  "Opciones de precio (base)",
);

export const PricingTiersBuilderPlaceholder = createPlaceholderAction(
  "offer-pricing-tiers-builder",
  "Tiers de precio por edición",
);

export const KnowledgeUploaderPlaceholder = createPlaceholderAction(
  "offer-knowledge-uploader",
  "Subida de documentos de conocimiento",
);

export const InstructorsPickerPlaceholder = createPlaceholderAction(
  "offer-instructors-picker",
  "Selector de instructores",
);

export const GallerySingleImagePlaceholder = createPlaceholderAction(
  "offer-gallery-single-image",
  "Imagen única",
);

export const GalleryMultiImagePlaceholder = createPlaceholderAction(
  "offer-gallery-multi-image",
  "Galería múltiple",
);

export const PaymentProviderPickerPlaceholder = createPlaceholderAction(
  "payment-provider-picker",
  "Métodos de pago (desde Conexiones)",
);

export const SchedulingEventTypePickerPlaceholder = createPlaceholderAction(
  "scheduling-event-type-picker",
  "Tipo de evento (desde Agenda)",
);

export const SocialProofPickerPlaceholder = createPlaceholderAction(
  "offer-social-proof-picker",
  "Testimonios (desde Brand Vault)",
);

export const ValueStackBuilderPlaceholder = createPlaceholderAction(
  "offer-value-stack-builder",
  "Value stack builder",
);

export const FAQBuilderPlaceholder = createPlaceholderAction(
  "offer-faq-builder",
  "Constructor de FAQ",
);

export const EditionPricingOverridePlaceholder = createPlaceholderAction(
  "offer-edition-pricing-override",
  "Override de precio por edición",
);
