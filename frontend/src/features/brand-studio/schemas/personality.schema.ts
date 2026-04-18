import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Personality section. The rich controls (preset catalog, dimension sliders,
 * clone-from-chat) are custom actions — a bare-bones set of text fields
 * exists as fallback for quick edits.
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
  ],
};
