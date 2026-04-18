import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Knowledge — documents and reference material that feed the sales agent's
 * retrieval pipeline. All material applies offer-wide; per-edition docs
 * (e.g. cohort syllabus) live on the edition assets tab.
 *
 * The ``documents`` field renders via a custom uploader action registered
 * in ``actions/registry.ts`` — the runtime stores file references, the
 * action handles upload + progress + removal.
 */
export const offerKnowledgeSchema: SectionSchema = {
  key: "offer.knowledge",
  title: "Conocimiento",
  description: "Documentos y materiales que alimentan al agente de ventas.",
  scope: "offer_level",
  fields: [
    {
      id: "documents",
      label: "Documentos base",
      type: "custom",
      path: "knowledge_documents",
      action: "offer-knowledge-uploader",
      hint: "PDFs, notas, FAQ, testimonios en texto. Se indexan para búsqueda semántica.",
    },
    {
      id: "reference_urls",
      label: "URLs de referencia",
      type: "textarea",
      path: "knowledge_reference_urls",
      rows: 4,
      hint: "Una URL por línea. Landings propias, posts, videos propios. El SDR puede citarlas.",
    },
    {
      id: "faq",
      label: "Preguntas frecuentes",
      type: "array",
      path: "faq",
      hint: "FAQs priorizadas. El SDR las responde antes de que el lead las tenga que preguntar.",
      itemSchema: {
        description: "Una pregunta y su respuesta oficial.",
        fields: [
          { id: "question", label: "Pregunta", type: "text", path: "question", required: true },
          {
            id: "answer",
            label: "Respuesta",
            type: "textarea",
            path: "answer",
            rows: 3,
            required: true,
          },
        ],
      },
    },
  ],
};
