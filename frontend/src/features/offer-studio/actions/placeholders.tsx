"use client";

/**
 * Placeholder action components.
 *
 * Each ``custom`` field in an offer-studio schema references an action key
 * (see ``hint`` attrs in ``schemas/*.schema.ts``). Phase C declares the
 * contract without delivering the action UI — Phase E ports each legacy
 * ``*Form.tsx`` / ``*Manager.tsx`` as the real implementation, one at a
 * time, replacing the placeholder entry in ``registry.ts``.
 *
 * Until then, the placeholder renders a muted "pendiente" card so the
 * editor is inspectable end-to-end without crashing when a schema mounts
 * a not-yet-ported action. Matches the pattern from brand-studio Sprint 1.
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
        de portar (Sprint 6 Fase E).
      </p>
    </div>
  );
}

/** Create a bound placeholder so consumers mount a ready-to-render component. */
export function createPlaceholderAction(actionKey: string, label: string) {
  return function Placeholder(): ReactElement {
    return <ActionPlaceholder label={label} actionKey={actionKey} />;
  };
}

/**
 * List of action keys referenced by the offer-studio schemas. Registered
 * at module load so every schema parses and renders. Phase E replaces
 * individual entries with real implementations.
 */
export const PLACEHOLDER_ACTIONS: readonly { key: string; label: string }[] = [
  { key: "offer-pricing-options-builder", label: "Opciones de precio (base)" },
  { key: "offer-pricing-tiers-builder", label: "Tiers de precio por edición" },
  { key: "offer-knowledge-uploader", label: "Subida de documentos de conocimiento" },
  { key: "offer-instructors-picker", label: "Selector de instructores" },
  { key: "offer-gallery-single-image", label: "Imagen única" },
  { key: "offer-gallery-multi-image", label: "Galería múltiple" },
  // Latam rollout — Sprint 8+ (referenced from pricing.schema + location.schema)
  { key: "payment-provider-picker", label: "Métodos de pago (desde Conexiones)" },
  { key: "scheduling-event-type-picker", label: "Tipo de evento (desde Agenda)" },
];
