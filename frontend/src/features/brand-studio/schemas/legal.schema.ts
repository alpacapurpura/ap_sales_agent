import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Brand-studio ▸ Legal section.
 *
 * All fields persist to ``BrandIdentity`` (same slice as the Identidad
 * section). Splitting them into their own section keeps Identidad focused on
 * narrative/operational data while giving compliance its own editable surface
 * with per-field autosave — the previous monolithic LegalAction modal is
 * retired.
 *
 * Grouped visually in three tiers:
 *   1. Fiscal core                    (razón social, entidad, RUC, dirección)
 *   2. Contacto + URLs legales        (notificaciones, términos, cookies…)
 *   3. Profesión regulada + guardrails del sales agent (opcional)
 *
 * The guardrail fields (``sales_agent_disclaimer``,
 * ``sales_agent_out_of_scope``, ``escalation_contact``) are internal to the
 * agent prompt assembly — they bound what the agent can claim on behalf of
 * regulated professionals (consultorios médicos, estudios legales, coaches
 * certificados) without exposing the guardrail list to leads.
 */
export const legalSchema: SectionSchema = {
  key: "brand.legal",
  title: "Legal y cumplimiento",
  description:
    "Datos fiscales, políticas y límites operativos del negocio. El agente usa esta información para facturar correctamente, responder dudas de cumplimiento y mantenerse dentro del alcance permitido.",
  fields: [
    // ─── Fiscal core ─────────────────────────────────────────────────────
    {
      id: "legal_name",
      label: "Razón social",
      type: "text",
      path: "legal_name",
      placeholder: "Ej: Visionarias LLC",
      hint: "Nombre legal registrado de la empresa. Aparece en facturas y contratos.",
    },
    {
      id: "legal_entity_type",
      label: "Tipo de entidad",
      type: "enum",
      path: "legal_entity_type",
      hint: "Figura jurídica bajo la que opera el negocio. El agente la usa para adaptar el lenguaje de facturación.",
      options: [
        { value: "persona_natural", label: "Persona natural / autónomo" },
        { value: "monotributo", label: "Monotributo (AR)" },
        { value: "sac", label: "S.A.C. — Sociedad Anónima Cerrada" },
        { value: "sas", label: "S.A.S. — Sociedad por Acciones Simplificada" },
        { value: "sa", label: "S.A. — Sociedad Anónima" },
        { value: "srl", label: "S.R.L. — Sociedad de Responsabilidad Limitada" },
        { value: "eirl", label: "E.I.R.L. — Empresa Individual de Resp. Limitada" },
        { value: "llc", label: "LLC / Corp (EE.UU. y offshore)" },
        { value: "otro", label: "Otro" },
      ],
    },
    {
      id: "tax_id",
      label: "Identificación fiscal",
      type: "text",
      path: "tax_id",
      placeholder: "Ej: 20601234567",
      hint: "RUC (PE), RFC (MX), NIT (CO), CUIT (AR), EIN (US). Incluye el país si es ambiguo.",
    },
    {
      id: "tax_regime",
      label: "Régimen tributario",
      type: "text",
      path: "tax_regime",
      placeholder: "Ej: Régimen General, RESICO, Monotributo Cat. B",
      hint: "Régimen bajo el que facturas. Varía por país: NRUS/RER/General (PE), RESICO/PF/PM (MX), Monotributo/Responsable Inscripto (AR), Simple/Común (CO).",
    },
    {
      id: "country_of_registration",
      label: "País de registro",
      type: "text",
      path: "country_of_registration",
      placeholder: "Ej: Perú, México, Colombia",
      hint: "Jurisdicción donde está legalmente constituido el negocio. Define qué ley aplica en disputas.",
    },
    {
      id: "commercial_registry_number",
      label: "Registro mercantil",
      type: "text",
      path: "commercial_registry_number",
      placeholder: "Ej: Partida 12345678 SUNARP",
      hint: "Número de inscripción en SUNARP, Cámara de Comercio, Registro Público de Comercio o equivalente.",
    },
    {
      id: "fiscal_address",
      label: "Dirección fiscal",
      type: "textarea",
      path: "fiscal_address",
      rows: 2,
      hint: "Dirección registrada ante la autoridad tributaria. Aparece en facturas formales.",
    },
    {
      id: "legal_representative",
      label: "Representante legal",
      type: "text",
      path: "legal_representative",
      placeholder: "Nombre completo",
      hint: "Persona con poderes de firma para contratos y actos legales.",
    },

    // ─── Contacto legal ──────────────────────────────────────────────────
    {
      id: "legal_email",
      label: "Email de notificaciones legales",
      type: "email",
      path: "legal_email",
      placeholder: "legal@tumarca.com",
      hint: "Canal para notificaciones formales (burofax, demandas, requerimientos). Idealmente distinto al email de soporte.",
    },
    {
      id: "dpo_email",
      label: "Email de protección de datos (DPO)",
      type: "email",
      path: "dpo_email",
      placeholder: "privacidad@tumarca.com",
      hint: "Oficial de Protección de Datos. Exigido por Ley 29733 (PE), LFPDPPP (MX), Habeas Data (CO). Puede ser el mismo que legal_email si no tienes DPO dedicado.",
    },

    // ─── URLs legales ────────────────────────────────────────────────────
    {
      id: "terms_url",
      label: "Términos y condiciones",
      type: "url",
      path: "terms_url",
      placeholder: "https://tumarca.com/terminos",
      hint: "URL pública del documento de términos. El agente la comparte cuando el lead pregunta por condiciones de servicio.",
    },
    {
      id: "privacy_url",
      label: "Política de privacidad",
      type: "url",
      path: "privacy_url",
      placeholder: "https://tumarca.com/privacidad",
      hint: "URL pública. Obligatoria si capturas datos personales (todo lead capture lo hace).",
    },
    {
      id: "cookies_url",
      label: "Política de cookies",
      type: "url",
      path: "cookies_url",
      placeholder: "https://tumarca.com/cookies",
      hint: "Exigida por GDPR si tu sitio recibe tráfico de la Unión Europea. Opcional para tráfico 100% Latam.",
    },
    {
      id: "refund_policy_url",
      label: "Política de reembolso",
      type: "url",
      path: "refund_policy_url",
      placeholder: "https://tumarca.com/reembolsos",
      hint: "URL pública. Clave para e-commerce, infoproductos y membresías: el agente la usa para cerrar objeciones de riesgo.",
    },
    {
      id: "acceptable_use_url",
      label: "Política de uso aceptable",
      type: "url",
      path: "acceptable_use_url",
      placeholder: "https://tumarca.com/uso-aceptable",
      hint: "Aplica si tu producto es SaaS, comunidad o plataforma con contenido generado por usuarios.",
    },

    // ─── Profesión regulada ──────────────────────────────────────────────
    {
      id: "regulated_profession_body",
      label: "Colegio o ente regulador",
      type: "text",
      path: "regulated_profession_body",
      placeholder: "Ej: Colegio Médico del Perú, INDECOPI, CONDUSEF",
      hint: "Entidad que regula tu profesión o sector. Completa solo si aplica (salud, legal, financiero, inmobiliario, psicología, nutrición, arquitectura, contaduría).",
    },
    {
      id: "professional_license_number",
      label: "Colegiatura o matrícula",
      type: "text",
      path: "professional_license_number",
      placeholder: "Ej: CMP 45678",
      hint: "Número de colegiatura, cédula profesional o matrícula. El agente lo menciona solo si el lead pregunta por credenciales.",
    },
    {
      id: "professional_license_holder",
      label: "Titular de la colegiatura",
      type: "text",
      path: "professional_license_holder",
      placeholder: "Nombre del profesional colegiado",
      hint: "Completa solo si el colegiado es distinto al representante legal (ej: clínica donde el director médico no es el dueño).",
    },
    {
      id: "operating_authorization",
      label: "Autorización de funcionamiento",
      type: "textarea",
      path: "operating_authorization",
      rows: 2,
      placeholder: "Ej: Resolución Directoral 0123-2024-DIRIS vigente hasta 2027-03-15",
      hint: "Licencia de establecimiento regulado: MINSA/SUSALUD (PE), COFEPRIS (MX), Invima (CO), ANMAT (AR). Incluye número y vigencia para que el agente evite promesas si la autorización expiró.",
    },
    {
      id: "liability_insurance_carrier",
      label: "Seguro de responsabilidad civil profesional",
      type: "text",
      path: "liability_insurance_carrier",
      placeholder: "Ej: Pacífico Seguros — Póliza de mala praxis",
      hint: "Solo el nombre de la aseguradora. El agente sabe que existe cobertura pero nunca divulga número de póliza, suma asegurada ni detalles.",
    },

    // ─── Sales-agent guardrails (internos) ───────────────────────────────
    {
      id: "sales_agent_disclaimer",
      label: "Aviso obligatorio del agente",
      type: "textarea",
      path: "sales_agent_disclaimer",
      rows: 3,
      placeholder:
        "Ej: La información compartida por este canal es orientativa. Toda atención clínica requiere consulta presencial con un profesional colegiado.",
      hint: "Texto que el agente de ventas DEBE incluir al inicio o cierre de conversaciones. Es visible al lead. Úsalo para delimitar expectativas y proteger al negocio de malinterpretaciones.",
    },
    {
      id: "sales_agent_out_of_scope",
      label: "Temas fuera del alcance del agente",
      type: "textarea",
      path: "sales_agent_out_of_scope",
      rows: 5,
      placeholder:
        "diagnóstico clínico\nrecetas o dosis\nemergencias médicas\nsegunda opinión\ncobertura de seguro\nprecios exactos de procedimientos",
      hint: "Uno por línea. Lista interna — el agente la usa para detectar cuándo derivar a un humano, pero nunca la muestra al lead. Ejemplos: diagnósticos, consejo legal puntual, recomendación de inversión.",
    },
    {
      id: "escalation_contact",
      label: "Contacto de escalamiento",
      type: "text",
      path: "escalation_contact",
      placeholder: "Ej: WhatsApp del director / email de guardia",
      hint: "Canal al que el agente deriva cuando detecta un tema fuera de alcance. Puede ser un número, email o nombre de equipo — el agente dice 'te conecto con el equipo' sin exponer este dato.",
    },
  ],
};
