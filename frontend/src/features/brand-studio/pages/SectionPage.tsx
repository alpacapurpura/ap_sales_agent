"use client";

import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { SectionPage as SharedSectionPage } from "@/lib/studio-section-page";

import type { SectionSchema } from "@/lib/form-runtime/schema";

export interface SectionPageProps<TSlice extends object> {
  /** URL slug que identifica la sección (p.ej. "identity", "visuals"). */
  sectionSlug: string;
  /** Schema del form-runtime describiendo los fields. */
  schema: SectionSchema;
  /** Slice actual; `undefined`/`null` mientras carga. */
  values: TSlice | null | undefined;
  /** Save wireado a la mutación del feature. Recibe el slice compuesto. */
  onSave: (next: TSlice) => Promise<void>;
  /** Forward al loading state del runtime. */
  isLoading?: boolean;
  className?: string;
}

/**
 * Shim brand-studio sobre `lib/studio-section-page/SectionPage`.
 * Resuelve routing via `useBrandStudioFieldRouting(sectionSlug)` y delega
 * al shared presentacional.
 *
 * Mantiene la firma histórica (sin `activeFieldId` ni `getFieldHref` en
 * props) para que el factory en `section-pages.tsx` siga funcionando.
 * Post Fase 2 cada per-section file pasa a consumir directamente
 * `@/lib/studio-section-page` y este shim se elimina.
 *
 * Contrato de ruta (owned por el Server Component en `app/.../`):
 *   `/{tenantId}/brand-studio/{sectionSlug}`                  → list view
 *   `/{tenantId}/brand-studio/{sectionSlug}?field={fieldId}`  → detail view
 */
export function SectionPage<TSlice extends object>({
  sectionSlug,
  schema,
  values,
  onSave,
  isLoading,
  className,
}: SectionPageProps<TSlice>) {
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(sectionSlug);

  return (
    <SharedSectionPage<TSlice>
      sectionSlug={sectionSlug}
      schema={schema}
      values={values}
      onSave={onSave}
      isLoading={isLoading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      className={className}
    />
  );
}
