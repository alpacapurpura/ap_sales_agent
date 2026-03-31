import { Offer, OfferType } from "../types";
import { getSectionsForOffer } from "../config/offer-builder-config";

export interface SectionHealth {
  status: "complete" | "incomplete" | "optional";
  message?: string;
}

export interface OfferHealth {
  completionPercentage: number;
  sections: Record<string, SectionHealth>;
  missingFields: string[];
}

/**
 * Valida una sección específica de la oferta.
 */
const validateSection = (sectionId: string, offer: Offer): SectionHealth => {
  switch (sectionId) {
    case "identity":
      // Requerido: Nombre, Tipo, Nivel
      if (!offer.name || !offer.type || !offer.value_level) {
        return { status: "incomplete", message: "Faltan datos básicos" };
      }
      return { status: "complete" };

    case "strategy":
      // Requerido: Avatar match o Pain points
      if ((!offer.target_avatar_match || offer.target_avatar_match.length === 0) && 
          (!offer.marketing_pain_points || offer.marketing_pain_points.length === 0)) {
        return { status: "incomplete", message: "Definir estrategia o avatar" };
      }
      return { status: "complete" };

    case "psychology":
      // Requerido: Pain points y Desires
      if ((!offer.marketing_pain_points || offer.marketing_pain_points.length === 0) || 
          (!offer.marketing_desires || offer.marketing_desires.length === 0)) {
        return { status: "incomplete", message: "Faltan puntos de dolor/deseo" };
      }
      return { status: "complete" };

    case "promise":
      // Requerido: Promesa principal
      if (!offer.headline_promise) {
        return { status: "incomplete", message: "Falta la promesa principal" };
      }
      return { status: "complete" };

    case "pricing":
      // Requerido: Al menos una opción de precio
      if (!offer.pricing || offer.pricing.length === 0) {
        return { status: "incomplete", message: "Sin precio definido" };
      }
      return { status: "complete" };

    case "closing":
      // Requerido: Garantía
      if (!offer.guarantee_type) {
        return { status: "incomplete", message: "Definir garantía" };
      }
      return { status: "complete" };

    case "product_details":
    case "service_details":
    case "program_details":
    case "event_details":
    case "subscription_details":
      // Requerido: Detalles específicos presentes
      if (!offer.specific_details || Object.keys(offer.specific_details).length === 0) {
        return { status: "incomplete", message: "Faltan detalles específicos" };
      }
      return { status: "complete" };
    
    case "instructors":
      if (offer.instructors && offer.instructors.length > 0) {
        return { status: "complete" };
      }
      return { status: "optional" };

    case "resources":
    case "gallery":
    case "value_stack":
      // Opcionales por defecto o lógica simple
      return { status: "optional" };

    default:
      return { status: "optional" };
  }
};

/**
 * Calcula la salud (completitud) de una oferta basada en su tipo y configuración.
 */
export function getOfferHealth(offer: Offer, type: OfferType): OfferHealth {
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

  const completionPercentage = totalRequired > 0 
    ? Math.round((completedCount / totalRequired) * 100) 
    : 100; // Si no hay requeridos, está "completo" o es trivial

  return {
    completionPercentage,
    sections: sectionHealths,
    missingFields,
  };
}
