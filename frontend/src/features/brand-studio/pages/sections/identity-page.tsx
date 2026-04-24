"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { identitySchema } from "@/features/brand-studio/schemas/identity.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandIdentity } from "@/features/brand-studio/types";

/**
 * Identity section page. Code-split por chunk via `next/dynamic` en
 * `SectionDispatcher.tsx` — solo se compila cuando el usuario navega a
 * `/{tenantId}/brand-studio/identity`.
 */
export function IdentityPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("identity");

  return (
    <SectionPage<BrandIdentity>
      sectionSlug="identity"
      schema={identitySchema}
      values={hook.settings?.identity ?? undefined}
      onSave={async (next) => {
        await hook.updateIdentity(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
