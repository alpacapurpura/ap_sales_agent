import type { SectionSchema } from "@/lib/form-runtime/schema";

export const voiceSchema: SectionSchema = {
  key: "brand.voice",
  title: "Tono y voz",
  description: "Cómo se comunica tu marca en cada canal.",
  fields: [
    {
      id: "voice_tone",
      label: "Tono de voz",
      type: "textarea",
      path: "voice_tone",
      rows: 4,
      hint: "Describe el carácter de tus mensajes (cercano, experto, irreverente…).",
    },
    {
      id: "voice_clone",
      label: "Clonación desde texto o archivo",
      type: "custom",
      path: "voice_tone",
      action: "voice-clone",
      hint: "La IA detecta patrones, vocabulario, ritmo y actualiza el tono arriba.",
    },
  ],
};
