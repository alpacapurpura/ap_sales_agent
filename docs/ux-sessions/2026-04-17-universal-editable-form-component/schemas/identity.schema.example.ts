/**
 * EXAMPLE schema for the Brand Identity section.
 *
 * This file lives in the UX session folder as a reference for the user
 * to review before Sprint 1 begins. In Sprint 1, the real schema will
 * be written into `features/brand-studio/schemas/identity.schema.ts`
 * and will be imported by `features/brand-studio/pages/EsenciaPage.tsx`.
 *
 * Purpose: show how a complete section collapses into a schema +
 * a data hook, replacing the current
 * identity-preview.tsx + identity-form.tsx + identity-manager.tsx
 * triplet plus its entry in EditSheetManager.
 */

import type { SectionSchema } from "@/lib/form-runtime/schema/types";

export const identitySchema: SectionSchema = {
  key: "brand.identity",
  title: "Identidad",
  description:
    "Los cimientos de tu marca. El sales agent usará esto como ancla narrativa.",
  fields: [
    {
      id: "name",
      label: "Nombre",
      type: "text",
      path: "name",
      required: true,
      placeholder: "Ej: Visionarias",
    },
    {
      id: "tagline",
      label: "Tagline",
      type: "text",
      path: "tagline",
      hint: "Una línea que resume tu propuesta. Pensalo como el subtítulo de un libro.",
      placeholder: "Creadoras que viven de lo que aman",
    },
    {
      id: "mission",
      label: "Misión",
      type: "textarea",
      path: "mission",
      rows: 4,
      hint: "El porqué detrás de tu marca. Máximo 2 oraciones.",
      placeholder:
        "Ej: Ayudar a creadoras digitales a transformar su audiencia en clientes recurrentes…",
    },
    {
      id: "vision",
      label: "Visión",
      type: "textarea",
      path: "vision",
      rows: 3,
      hint: "Dónde querés estar en 3–5 años.",
    },
    {
      id: "voice_tone",
      label: "Tono de voz",
      type: "textarea",
      path: "voice_tone",
      rows: 2,
      hint: "Describe cómo habla tu marca. El SDR usará este tono en todas sus conversaciones.",
      placeholder:
        "Ej: Conversacional, aspiracional, directo con toques de humor",
    },
    {
      // This field delegates to the ported VoiceCloneAction action.
      // The action receives { value, onChange, props }.
      // Props are schema-defined and immutable.
      id: "voice_tone_clone",
      label: "Clonación de estilo (IA)",
      type: "custom",
      path: "voice_tone", // writes back into the same field as above
      action: "voice-clone",
      hint: "Pegá texto tuyo o subí un archivo. La IA detecta tu tono y lo guarda acá arriba.",
    },
    {
      id: "brand_archetype",
      label: "Arquetipo",
      type: "enum",
      path: "brand_archetype",
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
      id: "website",
      label: "Sitio web",
      type: "url",
      path: "website",
      placeholder: "https://…",
    },
  ],
};

/**
 * How the page consumes the schema (Sprint 1, in features/brand-studio/pages/EsenciaPage.tsx):
 *
 * import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
 * import { UniversalEditableSection } from "@/components/form-runtime/UniversalEditableSection";
 * import { identitySchema } from "@/features/brand-studio/schemas/identity.schema";
 *
 * export function EsenciaPage() {
 *   const { settings, isLoading, updateIdentity } = useBrandSettings();
 *   return (
 *     <UniversalEditableSection
 *       schema={identitySchema}
 *       values={settings?.identity ?? {}}
 *       onSave={updateIdentity}
 *       isLoading={isLoading}
 *     />
 *   );
 * }
 *
 * ---
 *
 * What disappears when this ships:
 *   - features/brand/sections/identity/identity-preview.tsx
 *   - features/brand/sections/identity/identity-form.tsx
 *   - features/brand/sections/identity/identity-manager.tsx
 *   - "identity" entry in features/brand/components/forms/EditSheetManager.tsx
 *   - "identity" entry in features/brand/config/sections.ts EDIT_MODE_META
 */
