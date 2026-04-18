import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Knowledge — material interno que alimenta al agente de ventas (retrieval
 * semántico). PDFs, notas técnicas, URLs propias. Las FAQs públicas
 * visibles al cliente viven en la sección FAQ separada y se indexan
 * automáticamente junto con los documentos base.
 *
 * Toda la documentación aplica a nivel offer. Material específico de una
 * edición (ej. syllabus de cohorte Q2) vive en ``resources`` como
 * edition_resources.
 */
export const offerKnowledgeSchema: SectionSchema = {
  key: "offer.knowledge",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "documents",
      label: "Documentos base",
      type: "custom",
      path: "knowledge_documents",
      action: "offer-knowledge-uploader",
      hint: "PDFs, notas técnicas, guías internas, testimonios largos en texto. Se indexan para búsqueda semántica del agente de ventas. Todo lo que cargues acá puede ser citado por el agente para responder preguntas técnicas.",
    },
    {
      id: "reference_urls",
      label: "URLs de referencia",
      type: "textarea",
      path: "knowledge_reference_urls",
      rows: 4,
      placeholder: "https://tusitio.com/caso-exito-maria\nhttps://youtube.com/watch?v=... (charla sobre el método)",
      hint: "Una URL por línea. Landings propias, posts, videos propios, notas de prensa. El agente puede citarlas durante la conversación de venta.",
    },
  ],
};
