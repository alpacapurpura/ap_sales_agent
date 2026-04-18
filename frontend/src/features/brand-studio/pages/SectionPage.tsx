"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";

import type { SectionSchema } from "@/lib/form-runtime/schema";

export interface SectionPageProps<TSlice extends object> {
  /** URL slug that identifies this section (e.g. "identity", "visuals"). */
  sectionSlug: string;
  /** Form-runtime schema describing the section's fields. */
  schema: SectionSchema;
  /** Current slice from the backend; pass `undefined`/`null` while loading. */
  values: TSlice | null | undefined;
  /** Save function wired to the feature's mutation. Receives the composed slice. */
  onSave: (next: TSlice) => Promise<void>;
  /** Forwarded to the runtime's loading state. */
  isLoading?: boolean;
  /** Optional CTA to invoke a guided copilot interview. */
  onStartInterview?: () => void;
  className?: string;
}

/**
 * Presentational section page. Reads `activeFieldId` + builds `getFieldHref`
 * from the URL via `useBrandStudioFieldRouting`, then delegates everything
 * else to `UniversalEditableSection`. Consumers compose this with the
 * specific schema + slice selector + onSave their feature exposes.
 *
 * Route contract (owned by the consumer page file in `app/.../`):
 *   /{tenantId}/brand-studio/{sectionSlug}              → list view
 *   /{tenantId}/brand-studio/{sectionSlug}/{fieldId}    → detail view
 */
export function SectionPage<TSlice extends object>({
  sectionSlug,
  schema,
  values,
  onSave,
  isLoading,
  onStartInterview,
  className,
}: SectionPageProps<TSlice>) {
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(sectionSlug);

  return (
    <UniversalEditableSection
      schema={schema}
      values={values}
      onSave={onSave}
      isLoading={isLoading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      onStartInterview={onStartInterview}
      className={className}
    />
  );
}
