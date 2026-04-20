import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Buyer personas (called "avatars" in product language). Each item is a
 * sub-entity created via a separate API — the array controls the list;
 * the rich action handles per-item creation/editing flows.
 */
export const avatarsSchema: SectionSchema = {
  key: "brand.avatars",
  title: "Buyer personas",
  description: "Perfiles arquetípicos de tu cliente ideal. El SDR los usa para segmentar.",
  fields: [
    {
      id: "avatar_action",
      label: "Crear / editar buyer persona",
      type: "custom",
      path: "buyer_personas",
      action: "avatar",
      hint: "Flujo guiado para capturar demografía, psicografía, pain points.",
    },
  ],
};
