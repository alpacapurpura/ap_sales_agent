"use client";

import { UniversalEditableSection } from "@/components/form-runtime";

import "@/features/brand-studio/actions/registry";

import { avatarsSchema } from "@/features/brand-studio/schemas";

/**
 * Public / buyer persona list landing. The avatars schema delegates to the
 * `avatar` custom action which will port in Sprint 2 (creates/edits sub-entities
 * via the buyer_persona API — schema fields are presentational only).
 */
export function PublicoPage() {
  return (
    <UniversalEditableSection
      schema={avatarsSchema}
      values={{}}
      onSave={async () => {
        // no-op: the custom action manages its own API calls
      }}
    />
  );
}
