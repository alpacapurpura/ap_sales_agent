import { getSectionsForOffer } from "../config/offer-builder-config";

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

/**
 * Valida una sección específica de la oferta.
 */
const validateSection = (sectionId: string, offer: Offer): SectionHealth => {
  switch (sectionId) {
    case "identity":
      return validateIdentity(offer);
    case "strategy":
      return validateStrategy(offer);
    case "psychology":
      return validatePsychology(offer);
    case "promise":
      if (!offer.headline_promise) {
        return { status: "incomplete", message: "Falta la promesa principal" };
      }
      return { status: "complete" };
    case "pricing":
      if (!offer.pricing || offer.pricing.length === 0) {
        return { status: "incomplete", message: "Sin precio definido" };
      }
      return { status: "complete" };
    case "closing":
      if (!offer.guarantee_type) {
        return { status: "incomplete", message: "Definir garantía" };
      }
      return { status: "complete" };
    case "product_details":
    case "service_details":
    case "program_details":
    case "event_details":
    case "subscription_details":
      return validateSpecificDetails(offer);
    case "instructors":
      return offer.instructors && offer.instructors.length > 0
        ? { status: "complete" }
        : { status: "optional" };
    case "resources":
    case "gallery":
    case "value_stack":
      return { status: "optional" };
    default:
      return { status: "optional" };
  }
};

/**
 * Calcula la salud (completitud) de una oferta basada en su tipo y configuración.
 */
export function getOfferHealth(offer: Offer): OfferHealth {
  const sections = getSectionsForOffer(offer);

  if (sections.length === 0) {
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

  sections.forEach((sectionId) => {
    const health = validateSection(sectionId, offer);
    sectionHealths[sectionId] = health;

    if (health.status !== "optional") {
      totalRequired++;
      if (health.status === "complete") {
        completedCount++;
      } else if (health.message) {
        missingFields.push(`${sectionId}: ${health.message}`);
      }
    }
  });

  const completionPercentage =
    totalRequired > 0 ? Math.round((completedCount / totalRequired) * 100) : 100; // Si no hay requeridos, está "completo" o es trivial

  return {
    completionPercentage,
    sections: sectionHealths,
    missingFields,
  };
}
