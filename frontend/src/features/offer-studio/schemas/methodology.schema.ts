import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Methodology — el framework o método propio con el que entregás
 * resultados. Diferenciador clave contra competidores: un método con
 * nombre propio es defensible y no replicable fácilmente.
 *
 * Latam: coaches, academias y agencias que venden "método" venden más
 * caro que los que venden "horas". Poné nombre memorable
 * ("Método SCAI", "Framework de 5 Etapas") — funciona como marca
 * registrada conceptual.
 */
export const offerMethodologySchema: SectionSchema = {
  key: "offer.methodology",
  scope: "offer_level",
  fields: [
    {
      id: "method_name",
      label: "Nombre del método",
      type: "text",
      path: "methodology_name",
      required: true,
      placeholder: "Método SCAI · Framework de 5 Etapas · Proceso ECCO",
      hint: "Un nombre memorable que puedas mencionar en cada contenido. Idealmente protegible como marca.",
    },
    {
      id: "method_tagline",
      label: "Frase que lo resume",
      type: "text",
      path: "methodology_tagline",
      placeholder: "El camino de 5 pasos para pasar de freelance a agencia",
      hint: "Una oración. Es lo que decís cuando te preguntan 'de qué se trata el método'.",
    },
    {
      id: "origin_story",
      label: "Cómo nació el método",
      type: "textarea",
      path: "methodology_origin",
      rows: 3,
      placeholder: "Después de 10 años atendiendo PYMES, identifiqué 5 patrones comunes que causaban estancamiento. El método encapsula las 5 intervenciones que los desbloquean.",
      hint: "El porqué del método. Le da autoridad — no salió de la nada, viene de años de práctica.",
    },
    {
      id: "phases",
      label: "Fases del método",
      type: "array",
      path: "methodology_phases",
      hint: "Cada fase: número, nombre, duración, entregable, qué aporta el cliente. Ordenadas secuencialmente.",
      itemSchema: {
        description: "Una fase del método.",
        fields: [
          {
            id: "name",
            label: "Nombre de la fase",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Fase 1: Diagnóstico estratégico",
          },
          {
            id: "duration",
            label: "Duración",
            type: "text",
            path: "duration",
            placeholder: "2 semanas · 4 sesiones · 1 día",
          },
          {
            id: "description",
            label: "Qué pasa en esta fase",
            type: "textarea",
            path: "description",
            rows: 2,
            placeholder: "Auditamos el pipeline actual, identificamos leaks y priorizamos las 3 intervenciones de mayor impacto.",
          },
          {
            id: "deliverable",
            label: "Entregable al final",
            type: "text",
            path: "deliverable",
            placeholder: "Reporte de diagnóstico + roadmap priorizado",
            hint: "Lo que el cliente tiene en mano al terminar esta fase.",
          },
          {
            id: "client_input",
            label: "Qué aporta el cliente",
            type: "text",
            path: "client_input",
            placeholder: "Acceso a CRM, 2 reuniones, responder cuestionario",
            hint: "Importante para set expectations y evitar fricción.",
          },
        ],
      },
    },
    {
      id: "principles",
      label: "Principios fundamentales",
      type: "textarea",
      path: "methodology_principles",
      rows: 4,
      placeholder: "1. Simple antes que completo\n2. Evidencia antes que opinión\n3. Iteración semanal",
      hint: "Los pilares filosóficos del método. Dan coherencia y personalidad.",
    },
    {
      id: "tools_used",
      label: "Herramientas propias (canvas, plantillas, frameworks)",
      type: "textarea",
      path: "methodology_tools",
      rows: 3,
      placeholder: "Canvas de Posicionamiento SCAI\nPlantilla de Auditoría Express\nScoring de Priorización",
      hint: "Lista uno por línea. Si tenés herramientas propias, son un asset diferenciador enorme.",
    },
  ],
};
