import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { SectionKey, VariantStructure } from "./archetype-catalog-api";
import type { OfferArchetype, OfferValueLevel } from "../types";

const API_URL = config.api.baseUrl;

/**
 * ExpertBusinessType values — MUST mirror
 * ``backend/src/shared/domain/expert_business_type.py`` verbatim.
 */
export type ExpertBusinessType =
  | "profesional_salud"
  | "consultor_profesional"
  | "coach_mentor"
  | "academia_infoproductor"
  | "anfitrion_productor"
  | "agencia_freelance"
  | "marca_ecommerce"
  | "negocio_local"
  | "software_saas";

/**
 * PresetFlag values — MUST mirror ``PresetFlag`` in
 * ``offer_type_preset_catalog.py`` verbatim. Flags are semantic signals the
 * wizard / landing generator / sales-agent read to adapt behavior without
 * hard-coding preset-by-preset logic.
 */
export type PresetFlag =
  | "supports_capacity"
  | "requires_start_date"
  | "delivery_hybrid"
  | "is_lead_magnet"
  | "recurring_billing"
  | "high_ticket";

/**
 * A binary refinement question surfaced after preset selection.
 *
 * ``on_yes_sections`` are appended to the preset's base_sections when the
 * user answers YES. De-duplication preserves the base order so sections
 * added by the preset itself stay on top of the editor rail.
 */
export interface ConditionalQuestion {
  readonly question_id: string;
  readonly question_es: string;
  readonly help_es: string;
  readonly on_yes_sections: readonly SectionKey[];
  readonly on_yes_flags: readonly PresetFlag[];
}

export interface OfferTypePreset {
  readonly preset_id: string;
  readonly business_type: ExpertBusinessType;
  /** Internal archetype tag — never shown to the user. Drives sales-agent
   *  grounding, analytics segmentation and fulfillment defaults. */
  readonly archetype: OfferArchetype;
  /** Sprint 15 — ladder rung this preset typically occupies. The wizard
   *  derives ``Offer.value_level`` from this after a preset pick, so the
   *  user never has to answer "¿en qué escalón del ladder?" directly. */
  readonly typical_value_level: OfferValueLevel;
  readonly label_es: string;
  readonly description_es: string;
  readonly icon_name: string;
  /** Ordered section list the editor renders by default. */
  readonly base_sections: readonly SectionKey[];
  /** IDs referencing entries in ``questions`` on the parent response. */
  readonly conditional_question_ids: readonly string[];
  readonly default_flags: readonly PresetFlag[];
  /** Latam-specific hint shown below the preset card in admin/help surfaces. */
  readonly suitability_note_es: string;
  readonly examples_es: readonly string[];
  /** Sprint 15.1 — optional preset-level override of the archetype's
   *  default variant structure. When set, the wizard skips the "¿cómo
   *  varía?" step and applies this structure directly (e.g.
   *  ``consultor_retainer`` forcing ``tier`` over ``recurring_intake``). */
  readonly default_variant_structure: VariantStructure | null;
}

export interface OfferTypePresetCatalogResponse {
  readonly version: string;
  readonly presets: readonly OfferTypePreset[];
  readonly questions: readonly ConditionalQuestion[];
}

function buildCatalogUrl(businessTypes: readonly ExpertBusinessType[]): string {
  if (!businessTypes.length) return `${API_URL}/api/v1/offer/type-presets/catalog`;
  const params = new URLSearchParams();
  for (const bt of businessTypes) params.append("business_types", bt);
  return `${API_URL}/api/v1/offer/type-presets/catalog?${params.toString()}`;
}

export const offerTypePresetCatalogApi = {
  fetch: async (
    businessTypes: readonly ExpertBusinessType[] = [],
  ): Promise<OfferTypePresetCatalogResponse> => {
    const res = await fetchClient(buildCatalogUrl(businessTypes));
    if (!res.ok) throw new Error("Failed to fetch offer-type preset catalog");
    return res.json() as Promise<OfferTypePresetCatalogResponse>;
  },

  fetchAll: async (): Promise<OfferTypePresetCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/type-presets/catalog/all`);
    if (!res.ok) throw new Error("Failed to fetch full offer-type preset catalog");
    return res.json() as Promise<OfferTypePresetCatalogResponse>;
  },
};

/**
 * Resolve the final ordered section list for a preset + answers.
 *
 * Pure function — mirrors the backend ``resolve_preset_sections`` so the
 * wizard can preview the section rail without a server roundtrip. Starts
 * from ``base_sections`` and appends sections contributed by YES-answered
 * conditional questions, preserving the base order and de-duplicating.
 */
export function resolvePresetSections(
  preset: OfferTypePreset,
  questions: readonly ConditionalQuestion[],
  answers: Readonly<Record<string, boolean>>,
): readonly SectionKey[] {
  const result: SectionKey[] = [...preset.base_sections];
  const registry = new Map(questions.map((q) => [q.question_id, q] as const));
  for (const qid of preset.conditional_question_ids) {
    if (!answers[qid]) continue;
    const question = registry.get(qid);
    if (!question) continue;
    for (const section of question.on_yes_sections) {
      if (!result.includes(section)) result.push(section);
    }
  }
  return result;
}

/**
 * Resolve the combined flags for a preset + answers. See
 * ``resolvePresetSections`` — same rules, on flags instead of sections.
 */
export function resolvePresetFlags(
  preset: OfferTypePreset,
  questions: readonly ConditionalQuestion[],
  answers: Readonly<Record<string, boolean>>,
): readonly PresetFlag[] {
  const result: PresetFlag[] = [...preset.default_flags];
  const registry = new Map(questions.map((q) => [q.question_id, q] as const));
  for (const qid of preset.conditional_question_ids) {
    if (!answers[qid]) continue;
    const question = registry.get(qid);
    if (!question) continue;
    for (const flag of question.on_yes_flags) {
      if (!result.includes(flag)) result.push(flag);
    }
  }
  return result;
}
