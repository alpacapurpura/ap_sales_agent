import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Personality section. Rich controls (preset catalog, dimension sliders,
 * clone-from-chat) are custom actions — the three simple fields below
 * (archetype, core_values, personality_traits) were moved out of the
 * legacy ``BrandPositioning.values`` block in Sprint 2.D and live here
 * end-to-end alongside the Personality Engine the Sales Agent consumes.
 */
export const personalitySchema: SectionSchema = {
  key: "brand.personality",
  title: "Personalidad",
  description: "Cómo siente tu marca. 6 presets o dimensiones finas.",
  fields: [
    {
      id: "preset_catalog",
      label: "Elegir un preset",
      type: "custom",
      path: "preset_key",
      action: "personality-presets",
      hint: "6 personalidades tipificadas. Elegí la más parecida y afiná después.",
    },
    {
      id: "dimensions",
      label: "Afinar dimensiones",
      type: "custom",
      path: "dimensions",
      action: "personality-dimensions",
      hint: "Sliders para energía, formalidad, directness, humor, emoción.",
    },
    {
      id: "clone_from_chat",
      label: "Clonar desde chat",
      type: "custom",
      path: "clone_source",
      action: "personality-clone",
      hint: "Pegá una conversación real y la IA reconstruye tu personalidad.",
    },
    {
      id: "archetype",
      label: "Arquetipo",
      type: "enum",
      path: "archetype",
      hint: "Arquetipo de Jung. Un solo valor.",
      options: [
        { value: "sage", label: "Sabio" },
        { value: "hero", label: "Héroe" },
        { value: "rebel", label: "Rebelde" },
        { value: "explorer", label: "Explorador" },
        { value: "creator", label: "Creador" },
        { value: "caregiver", label: "Cuidador" },
        { value: "ruler", label: "Gobernante" },
        { value: "magician", label: "Mago" },
        { value: "innocent", label: "Inocente" },
        { value: "jester", label: "Bufón" },
        { value: "lover", label: "Amante" },
        { value: "everyman", label: "Persona común" },
      ],
    },
    {
      id: "core_values",
      label: "Valores núcleo",
      type: "textarea",
      path: "core_values_text",
      rows: 3,
      hint: "Uno por línea. 3-5 valores que guían las decisiones de la marca.",
    },
    {
      id: "personality_traits",
      label: "Rasgos de personalidad",
      type: "textarea",
      path: "personality_traits_text",
      rows: 3,
      hint: "Uno por línea. Adjetivos cortos (ej: curiosa, auténtica, directa).",
    },
  ],
};
