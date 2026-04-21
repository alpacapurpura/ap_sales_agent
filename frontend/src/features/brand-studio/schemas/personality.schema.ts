import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Personality section. The three brand-archetype fields below (archetype,
 * core_values, personality_traits) persist to BrandIdentity and are consumed
 * by the Sales Agent. The rich controls for communication style (preset
 * catalog, dimension sliders, clone wizard) live in the top-level "Estilo
 * Comunicacional" section (slug: "estilo") backed by personality_profiles.
 */
export const personalitySchema: SectionSchema = {
  key: "brand.personality",
  title: "Personalidad",
  description: "Arquetipo y rasgos de marca que guían la identidad narrativa.",
  fields: [
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
