"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { identitySchema } from "@/features/brand-studio/schemas";

/**
 * Brand Studio → Esencia page. URL-driven per field; active field id comes
 * from the dynamic route segment. Sprint 2.0c will replace this with the
 * generic SectionPage factory.
 */
export function EsenciaPage() {
  const { settings, loading, updateIdentity } = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("esencia");

  return (
    <UniversalEditableSection
      schema={identitySchema}
      values={settings?.identity ?? {}}
      onSave={async (next) => {
        await updateIdentity(next);
      }}
      isLoading={loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
