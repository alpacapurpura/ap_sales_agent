"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { avatarsSchema } from "@/features/brand-studio/schemas";

/**
 * Public / buyer persona list landing. The avatars schema delegates to the
 * `avatar` custom action which Sprint 2.8 refactors (PersonaDetailView port).
 */
const NOOP_SAVE: () => Promise<void> = () => Promise.resolve();

/**
 *
 */
export function PublicoPage() {
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("publico");

  return (
    <UniversalEditableSection
      schema={avatarsSchema}
      values={{}}
      onSave={NOOP_SAVE}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
