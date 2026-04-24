import type { SaveMode, SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Props compartidos por los wrappers de sección de cualquier studio
 * (brand, offer, buyer-persona, landing…).
 *
 * El componente es presentacional: recibe routing (`activeFieldId` +
 * `getFieldHref`) ya resuelto y no depende del hook de field-routing del
 * studio. Cada per-section file del studio se encarga de llamar su hook
 * específico (`useBrandStudioFieldRouting`, `useOfferStudioFieldRouting`)
 * y pasa los valores como props. Esto rompe el acople
 * shared ↔ feature-specific y permite que el shared viva en `lib/`.
 */
export interface StudioSectionPageProps<TValues extends object> {
  /** Slug canónico de la sección (segmento estable de URL). */
  sectionSlug: string;
  /** Schema del form-runtime. Importado per-section para code-split real. */
  schema: SectionSchema;
  /** Slice actual resuelto; `undefined`/`null` mientras carga. */
  values: TValues | null | undefined;
  /** Save wireado a la mutación del feature. Recibe el slice completo. */
  onSave: (next: TValues) => Promise<void>;
  /** Field id activo, derivado del query param `?field=` o null en list view. */
  activeFieldId: string | null;
  /** Builder de href para field → URL del detalle o section-level si null. */
  getFieldHref: (fieldId: string | null) => string;
  /** Forward a UniversalEditableSection.isLoading. */
  isLoading?: boolean;
  /** Autosave modo (default del form-runtime o `autosave-with-banner` offer). */
  saveMode?: SaveMode;
  /** Override de título resuelto desde catálogo backend. Falla a schema.title. */
  titleOverride?: string;
  /** Override de descripción resuelto desde catálogo backend. */
  descriptionOverride?: string;
  /** Columna opcional entre rail y fields — collection sections. */
  instanceColumn?: React.ReactNode;
  className?: string;
}
