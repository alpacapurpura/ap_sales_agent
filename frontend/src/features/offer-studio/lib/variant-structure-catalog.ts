/**
 * Variant structure metadata — UI mirror of the backend
 * ``VariantStructureMetadata`` record.
 *
 * Used by the variant collection landing (card rendering), the wizard
 * "¿cómo varía tu oferta?" step, and the editor shell noun labels
 * ("Planes" / "Cohortes" / "Variantes" / etc.).
 *
 * The 8 structures cover every variant scenario in the catalog DAG:
 *   - 3 temporal: TEMPORAL_COHORT, TEMPORAL_SINGLE_DATE, RECURRING_INTAKE
 *   - 5 non-temporal: TIER, SKU_VARIANT, REGIONAL, MODALITY, LANGUAGE
 *
 * When a new structure is added on the backend it MUST be mirrored here.
 * The anti-drift test
 * ``src/__tests__/architecture/test-variant-structure-catalog-alignment``
 * fails CI if the backend catalog emits a key not listed here.
 */

import { Calendar, CalendarClock, Globe, Languages, Layers, MonitorSmartphone, Package, Users } from "lucide-react";

import type { VariantStructure } from "../api/archetype-catalog-api";

/** Card template used by the collection landing to render variants of this structure. */
export type VariantCardTemplate =
  | "temporal" // dates + capacity prominent
  | "tier" // price anchor + features differential
  | "sku" // attributes + inventory
  | "regional" // flag + currency + locale
  | "modality" // mode icon + logistics
  | "language"; // locale + translated copy

export interface VariantStructureUIMetadata {
  key: VariantStructure;
  labelEs: string;
  nounEs: string;
  nounPluralEs: string;
  descriptionEs: string;
  icon: React.ComponentType<{ className?: string }>;
  cardTemplate: VariantCardTemplate;
  /** Informational cardinality hint — drives wizard copy ("usually 2-5"). */
  cardinality: "singular" | "few" | "many";
  /** True iff publishing requires a concrete start_date. */
  requiresTemporalAnchor: boolean;
  /** True iff the structure exposes per-variant capacity (cupos / inventory). */
  supportsCapacity: boolean;
}

export const VARIANT_STRUCTURE_CATALOG: Record<VariantStructure, VariantStructureUIMetadata> = {
  temporal_cohort: {
    key: "temporal_cohort",
    labelEs: "Cohortes",
    nounEs: "cohorte",
    nounPluralEs: "cohortes",
    descriptionEs:
      "Grupos de alumnos que empiezan y terminan juntos en fechas fijas. Cada cohorte es una edición con fechas propias.",
    icon: Users,
    cardTemplate: "temporal",
    cardinality: "many",
    requiresTemporalAnchor: true,
    supportsCapacity: true,
  },
  temporal_single_date: {
    key: "temporal_single_date",
    labelEs: "Salidas",
    nounEs: "salida",
    nounPluralEs: "salidas",
    descriptionEs:
      "Un evento o experiencia en una fecha puntual (webinar, retiro, taller presencial).",
    icon: Calendar,
    cardTemplate: "temporal",
    cardinality: "singular",
    requiresTemporalAnchor: true,
    supportsCapacity: true,
  },
  recurring_intake: {
    key: "recurring_intake",
    labelEs: "Convocatorias",
    nounEs: "convocatoria",
    nounPluralEs: "convocatorias",
    descriptionEs:
      "Servicios que abren inscripciones en batches periódicos. Cada convocatoria es una edición con inicio agendado.",
    icon: CalendarClock,
    cardTemplate: "temporal",
    cardinality: "many",
    requiresTemporalAnchor: true,
    supportsCapacity: true,
  },
  tier: {
    key: "tier",
    labelEs: "Planes",
    nounEs: "plan",
    nounPluralEs: "planes",
    descriptionEs:
      "Niveles paralelos de la misma oferta con precio y beneficios distintos (Básico, Premium, Enterprise).",
    icon: Layers,
    cardTemplate: "tier",
    cardinality: "few",
    requiresTemporalAnchor: false,
    supportsCapacity: false,
  },
  sku_variant: {
    key: "sku_variant",
    labelEs: "Variantes",
    nounEs: "variante",
    nounPluralEs: "variantes",
    descriptionEs:
      "Versiones del mismo producto que se diferencian por atributos (talla, color, material). Cada variante tiene su propio SKU e inventario.",
    icon: Package,
    cardTemplate: "sku",
    cardinality: "many",
    requiresTemporalAnchor: false,
    supportsCapacity: true,
  },
  regional: {
    key: "regional",
    labelEs: "Regiones",
    nounEs: "región",
    nounPluralEs: "regiones",
    descriptionEs:
      "Misma oferta adaptada por país o región: precio, moneda, impuestos e idioma local.",
    icon: Globe,
    cardTemplate: "regional",
    cardinality: "few",
    requiresTemporalAnchor: false,
    supportsCapacity: false,
  },
  modality: {
    key: "modality",
    labelEs: "Modalidades",
    nounEs: "modalidad",
    nounPluralEs: "modalidades",
    descriptionEs:
      "Misma oferta entregada en formato distinto: presencial, online o híbrido. Cada modalidad tiene logística y a veces precio distinto.",
    icon: MonitorSmartphone,
    cardTemplate: "modality",
    cardinality: "few",
    requiresTemporalAnchor: false,
    supportsCapacity: true,
  },
  language: {
    key: "language",
    labelEs: "Idiomas",
    nounEs: "idioma",
    nounPluralEs: "idiomas",
    descriptionEs:
      "Misma oferta disponible en distintos idiomas. Cada idioma es una edición con copy y material traducidos.",
    icon: Languages,
    cardTemplate: "language",
    cardinality: "few",
    requiresTemporalAnchor: false,
    supportsCapacity: false,
  },
};

/** Return UI metadata for a variant structure, or undefined if unknown. */
export function getVariantStructureMeta(
  structure: VariantStructure | null | undefined,
): VariantStructureUIMetadata | undefined {
  if (!structure) return undefined;
  return VARIANT_STRUCTURE_CATALOG[structure];
}

/** Return the plural noun for the collection landing title — e.g. "Planes",
 *  "Cohortes", "Variantes". Falls back to "ediciones" defensively. */
export function getVariantNounPlural(structure: VariantStructure | null | undefined): string {
  return getVariantStructureMeta(structure)?.nounPluralEs ?? "ediciones";
}

/** Return the singular noun — "plan", "cohorte", "variante". */
export function getVariantNoun(structure: VariantStructure | null | undefined): string {
  return getVariantStructureMeta(structure)?.nounEs ?? "edición";
}

/** Return the human-readable label — "Planes", "Cohortes", etc. */
export function getVariantLabel(structure: VariantStructure | null | undefined): string {
  return getVariantStructureMeta(structure)?.labelEs ?? "Ediciones";
}
