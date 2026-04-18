import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Psychology — buying drivers + objections the sales agent must handle.
 *
 * Pure offer-level content: objection handling is consistent across editions.
 * Future "AI analysis" is deferred to Sprint 4d-h copilot tools; this schema
 * only covers the hand-authored fields the SDR reads at chat time.
 */
export const offerPsychologySchema: SectionSchema = {
  key: "offer.psychology",
  title: "Psicología y motores de compra",
  description: "Objeciones, creencias y disparadores de decisión del avatar.",
  scope: "offer_level",
  fields: [
    {
      id: "objections",
      label: "Objeciones conocidas",
      type: "textarea",
      path: "objections_raw",
      rows: 6,
      hint:
        "Uno por línea. Ej: 'No tengo tiempo', 'Es muy caro', 'Ya lo intenté antes'. " +
        "El SDR usa esto como primera línea de respuesta.",
    },
    {
      id: "emotional_triggers",
      label: "Disparadores emocionales",
      type: "textarea",
      path: "emotional_triggers",
      rows: 4,
      hint: "Miedos, deseos, identidades aspiracionales que mueven la decisión.",
    },
    {
      id: "status_drivers",
      label: "Motores de estatus",
      type: "textarea",
      path: "status_drivers",
      rows: 3,
      hint: "¿Qué cambia en cómo es percibido el cliente cuando compra?",
    },
    {
      id: "regret_scenarios",
      label: "Escenarios de arrepentimiento",
      type: "textarea",
      path: "regret_scenarios",
      rows: 3,
      hint: "Situaciones concretas en las que el avatar se arrepiente de NO haber comprado.",
    },
  ],
};
