import { OfferFormValues } from "../types/schema";

export const getSectionFields = (sectionId: string): (keyof OfferFormValues)[] => {
  switch (sectionId) {
    case "identity":
      return ["public_name", "internal_sku", "archetype", "status"];
    case "strategy":
      return ["target_avatar_match", "marketing_pain_points", "marketing_desires"];
    case "psychology":
      return ["marketing_pain_points", "marketing_desires"];
    case "promise":
      return ["headline_promise", "primary_outcome", "time_to_value"];
    case "pricing":
      return ["pricing_options", "currency"];
    case "closing":
      return ["guarantee_type", "guarantee_terms"];
    case "instructors":
      return ["instructors"];
    case "value_stack":
      return ["deliverables", "includes_offers"];
    case "resources":
      // Resources y Gallery comparten 'assets', pero filtrados en UI.
      // Al guardar, enviamos todo el array de assets para no perder los del otro tipo.
      return ["assets"];
    case "gallery":
      return ["assets"];
    case "program_details":
    case "product_details":
    case "service_details":
    case "event_details":
    case "subscription_details":
      return [
        "specific_details",
        "access_duration",
        "access_duration_text",
        "support_duration_days",
        "onboarding_action",
        "onboarding_url",
        "calendar_type_id",
        "checkout_page_url",
        "vsl_link",
      ];
    default:
      return [];
  }
};

/**
 * Extrae los datos relevantes para guardar una sección específica.
 * Maneja la lógica de preservación de objetos anidados (como specific_details)
 * asegurando que se envíe el objeto completo del estado actual.
 */
export const getSectionData = (
  sectionId: string,
  allValues: OfferFormValues,
): Partial<OfferFormValues> => {
  const fields = getSectionFields(sectionId);
  const data: Partial<OfferFormValues> = {};

  fields.forEach((field) => {
    // Skip special handling fields in the generic loop to avoid double assignment
    if (field === "specific_details" || field === "assets") return;

    // @ts-ignore
    data[field] = allValues[field];
  });

  // Lógica especial para asegurar integridad
  if (fields.includes("specific_details")) {
    // Asegurar que specific_details se envíe completo y manejar posibles nulos
    data.specific_details = allValues.specific_details ? { ...allValues.specific_details } : {};
  }

  if (fields.includes("assets")) {
    // Asegurar que assets se envíe completo
    data.assets = allValues.assets ? [...allValues.assets] : [];
  }

  return data;
};
