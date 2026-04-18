"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { identitySchema } from "@/features/brand-studio/schemas";

/**
 * Brand Studio → Esencia page. Sprint 1 renders the primary Identity
 * schema; Sprint 2 will add composition with voice, story, personality,
 * team, authority, testimonials, contact (the EsenciaView grouping).
 */
export function EsenciaPage() {
  const { settings, loading, updateIdentity } = useBrandSettings();

  return (
    <UniversalEditableSection
      schema={identitySchema}
      values={settings?.identity ?? {}}
      onSave={async (next) => {
        await updateIdentity(next);
      }}
      isLoading={loading}
    />
  );
}
