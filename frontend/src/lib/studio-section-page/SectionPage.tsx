"use client";

import { UniversalEditableSection } from "@/components/form-runtime";

import type { StudioSectionPageProps } from "./types";

/**
 * Wrapper presentacional compartido por brand-studio y offer-studio
 * (y futuros studios que usen el form-runtime).
 *
 * Delega render completo a `UniversalEditableSection`. El único rol de
 * este componente es ser el punto único de consumo desde las per-section
 * pages (`features/{studio}/pages/sections/*-page.tsx`) — centraliza la
 * invariante "un section page = un UniversalEditableSection".
 *
 * Cada per-section file del studio:
 *   1. Llama su hook de data (`useBrandSettings`, `useOfferSettings`…).
 *   2. Llama su hook de field-routing para obtener `activeFieldId` +
 *      `getFieldHref`.
 *   3. Llama `useSectionMetadata` si aplica.
 *   4. Pasa todo a `SectionPage`.
 *
 * Contrato de ruta lo mantiene el Server Component en `app/.../`:
 *   `/{tenantId}/{studio}/{…}/{sectionSlug}`                  → list view
 *   `/{tenantId}/{studio}/{…}/{sectionSlug}?field={fieldId}`  → detail view
 */
export function SectionPage<TValues extends object>({
  schema,
  values,
  onSave,
  activeFieldId,
  getFieldHref,
  isLoading,
  saveMode,
  titleOverride,
  descriptionOverride,
  instanceColumn,
  className,
}: StudioSectionPageProps<TValues>) {
  return (
    <UniversalEditableSection<TValues>
      schema={schema}
      values={values}
      onSave={onSave}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      isLoading={isLoading}
      saveMode={saveMode}
      titleOverride={titleOverride}
      descriptionOverride={descriptionOverride}
      instanceColumn={instanceColumn}
      className={className}
    />
  );
}
