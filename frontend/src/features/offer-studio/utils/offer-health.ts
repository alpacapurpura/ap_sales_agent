import type { Offer } from "../types";

export interface SectionHealth {
  status: "complete" | "incomplete" | "optional";
  message?: string;
}

export interface OfferHealth {
  completionPercentage: number;
  sections: Record<string, SectionHealth>;
  missingFields: string[];
}

function validateIdentity(offer: Offer): SectionHealth {
  if (!offer.name || !offer.archetype || !offer.value_level) {
    return { status: "incomplete", message: "Faltan datos básicos" };
  }
  return { status: "complete" };
}

function validateStrategy(offer: Offer): SectionHealth {
  const hasAvatar = offer.target_avatar_match && offer.target_avatar_match.length > 0;
  const hasPainPoints = offer.marketing_pain_points && offer.marketing_pain_points.length > 0;
  if (!hasAvatar && !hasPainPoints) {
    return { status: "incomplete", message: "Definir estrategia o avatar" };
  }
  return { status: "complete" };
}

function validatePsychology(offer: Offer): SectionHealth {
  const hasPain = offer.marketing_pain_points && offer.marketing_pain_points.length > 0;
  const hasDesires = offer.marketing_desires && offer.marketing_desires.length > 0;
  if (!hasPain || !hasDesires) {
    return { status: "incomplete", message: "Faltan puntos de dolor/deseo" };
  }
  return { status: "complete" };
}

function validateSpecificDetails(offer: Offer): SectionHealth {
  if (!offer.specific_details || Object.keys(offer.specific_details).length === 0) {
    return { status: "incomplete", message: "Faltan detalles específicos" };
  }
  return { status: "complete" };
}

function validatePromise(offer: Offer): SectionHealth {
  return offer.headline_promise
    ? { status: "complete" }
    : { status: "incomplete", message: "Falta la promesa principal" };
}

function validatePricing(offer: Offer): SectionHealth {
  return offer.pricing && offer.pricing.length > 0
    ? { status: "complete" }
    : { status: "incomplete", message: "Sin precio definido" };
}

function validateClosing(offer: Offer): SectionHealth {
  return offer.guarantee_type
    ? { status: "complete" }
    : { status: "incomplete", message: "Definir garantía" };
}

function validateInstructors(offer: Offer): SectionHealth {
  return offer.instructors && offer.instructors.length > 0
    ? { status: "complete" }
    : { status: "optional" };
}

const OPTIONAL_HEALTH: SectionHealth = { status: "optional" };
const alwaysOptional = (): SectionHealth => OPTIONAL_HEALTH;

/**
 * Per-section health rules. Dispatch table instead of a giant switch so each
 * rule reads as an isolated function and the complexity stays linear with the
 * section count. Unlisted keys fall through to ``OPTIONAL_HEALTH`` via
 * ``validateSection`` below.
 */
const SECTION_VALIDATORS: Record<string, (offer: Offer) => SectionHealth> = {
  identity: validateIdentity,
  strategy: validateStrategy,
  psychology: validatePsychology,
  promise: validatePromise,
  pricing: validatePricing,
  closing: validateClosing,
  product_details: validateSpecificDetails,
  service_details: validateSpecificDetails,
  program_details: validateSpecificDetails,
  event_details: validateSpecificDetails,
  subscription_details: validateSpecificDetails,
  instructors: validateInstructors,
  resources: alwaysOptional,
  gallery: alwaysOptional,
  value_stack: alwaysOptional,
};

/**
 * Validates the health of a single section against the offer's current data.
 *
 * Extracted so future consumers (schema runtime, copilot tools) can reuse
 * the same rules without pulling the whole health aggregation helper.
 * Unknown section keys resolve to ``optional`` so forward-compatible keys
 * from the backend catalog never break the UI.
 */
export function validateSection(sectionKey: string, offer: Offer): SectionHealth {
  return SECTION_VALIDATORS[sectionKey]?.(offer) ?? OPTIONAL_HEALTH;
}

/**
 * Aggregates section health into an overall completion percentage.
 *
 * The ``sectionKeys`` parameter is the ordered list of section identifiers
 * the offer's archetype surfaces — consumers pass it in from
 * ``useSectionsForArchetype(offer.archetype)`` so this helper stays pure
 * and the section ordering stays SSoT-aligned with the backend catalog.
 *
 * When ``sectionKeys`` is empty (e.g. archetype catalog still loading)
 * the result reports 0% with an explanatory missingFields entry so the
 * caller can still render a meaningful loading state.
 */
export function getOfferHealth(offer: Offer, sectionKeys: readonly string[]): OfferHealth {
  if (sectionKeys.length === 0) {
    return {
      completionPercentage: 0,
      sections: {},
      missingFields: ["Configuración de tipo de oferta no encontrada"],
    };
  }

  const sectionHealths: Record<string, SectionHealth> = {};
  let completedCount = 0;
  let totalRequired = 0;
  const missingFields: string[] = [];

  for (const sectionKey of sectionKeys) {
    const health = validateSection(sectionKey, offer);
    sectionHealths[sectionKey] = health;

    if (health.status !== "optional") {
      totalRequired++;
      if (health.status === "complete") {
        completedCount++;
      } else if (health.message) {
        missingFields.push(`${sectionKey}: ${health.message}`);
      }
    }
  }

  const completionPercentage =
    totalRequired > 0 ? Math.round((completedCount / totalRequired) * 100) : 100;

  return {
    completionPercentage,
    sections: sectionHealths,
    missingFields,
  };
}
