import { CommunityPlatform, LiveInteractionType, ProgramStructure } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * PROGRAMA archetype details — currículo, cohorte, compromiso del alumno.
 *
 * Scope MIXED: currículo + estructura + plataforma de comunidad son
 * offer-wide (cada cohorte corre el mismo programa). Fechas de inicio/fin,
 * capacidad y agenda concreta de sesiones en vivo viven en la
 * ``LaunchEdition`` (la cohorte específica).
 *
 * **Latam — decisiones de diseño:**
 * - ``weekly_time_commitment_hours`` es la pregunta que todo prospecto
 *   hace antes de comprar: "¿cuántas horas por semana?". Sin este número
 *   el agente de ventas improvisa y el alumno abandona a la semana 3.
 * - ``prerequisites_text`` reemplaza el enum legacy. En Latam los
 *   prerrequisitos son narrativos ("necesitas haber tomado el módulo X"
 *   o "recomendamos nivel intermedio de inglés") más que categóricos.
 * - ``is_application_required`` existía en el zod pero estaba oculto.
 *   Bootcamps y programas premium lo usan para filtrar leads y elevar
 *   exclusividad — ahora es editable.
 * - ``community_invite_link`` y ``lms_url`` existían en el zod pero no
 *   se exponían. Son entregables concretos post-checkout — sin ellos el
 *   onboarding se cae.
 */
export const offerProgramDetailsSchema: SectionSchema = {
  key: "offer.program_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "mixed",
  fields: [
    // ─── Estructura ───────────────────────────────────────────────────────
    {
      id: "structure_type",
      label: "Estructura del programa",
      type: "enum",
      path: "specific_details.structure_type",
      owner: "offer",
      options: [
        {
          value: ProgramStructure.FIXED_COHORT,
          label: "Cohorte con fechas fijas (arranque y cierre juntos)",
        },
        {
          value: ProgramStructure.ROLLING_ADMISSION,
          label: "Evergreen (entran cuando quieran, avanzan a su ritmo)",
        },
        {
          value: ProgramStructure.CHALLENGE,
          label: "Challenge intensivo (3-14 días de compromiso alto)",
        },
        {
          value: ProgramStructure.MEMBERSHIP,
          label: "Membresía académica (acceso continuo renovable)",
        },
      ],
      hint: "Cohorte fija maximiza accountability y completion rate (60-80%). Evergreen escala sin lanzamientos (30-40% completion). Challenge genera urgencia y preceden a ofertas pagas. Membresía es LTV recurrente.",
    },
    {
      id: "duration_weeks",
      label: "Duración total (semanas)",
      type: "number",
      path: "specific_details.duration_weeks",
      owner: "offer",
      placeholder: "8",
      hint: "Desde kickoff hasta última sesión. Bootcamp: 8-16 semanas. Challenge: 1-2 semanas. Programa anual: 52. Para evergreen, estimá semanas si avanzan al ritmo sugerido.",
    },
    {
      id: "weekly_time_commitment_hours",
      label: "Carga horaria semanal esperada (horas)",
      type: "number",
      path: "specific_details.weekly_time_commitment_hours",
      owner: "offer",
      placeholder: "4",
      hint: "Horas totales por semana que el alumno necesita dedicar (videos + práctica + sesiones en vivo + comunidad). Es la pregunta #1 que hacen antes de comprar. Sub-declarar genera churn; sobre-declarar frena la venta.",
    },

    // ─── Currículo ────────────────────────────────────────────────────────
    {
      id: "curriculum",
      label: "Currículo por módulo",
      type: "array",
      path: "specific_details.curriculum",
      owner: "offer",
      hint: "Los módulos en el orden que se dictan. Cada uno con título corto, resumen de 1-2 frases y los tópicos específicos cubiertos. Esta es la estructura que ve el alumno en la landing y la plataforma.",
      itemSchema: {
        description: "Un módulo del programa.",
        fields: [
          {
            id: "title",
            label: "Título del módulo",
            type: "text",
            path: "title",
            required: true,
            placeholder: "Módulo 3 — Fundamentos de pujas en Meta Ads",
            hint: "Nombre del módulo o clase. Se muestra en el temario de la landing y en el correo de bienvenida.",
          },
          {
            id: "description",
            label: "Descripción breve",
            type: "textarea",
            path: "description",
            rows: 2,
            placeholder:
              "Aprende a leer la subasta, elegir el objetivo correcto y evitar la trampa de la optimización de conversiones temprana.",
          },
          {
            id: "topics",
            label: "Tópicos cubiertos (uno por línea)",
            type: "textarea",
            path: "topics",
            rows: 4,
            placeholder:
              "CPM vs CPC: cuándo mirar cada uno\nEl mito del ROAS objetivo\nCómo escalar una campaña sin que se rompa\nCase study real: pasar de 1.5x a 4x ROAS en e-commerce",
          },
        ],
      },
    },

    // ─── Interacción + soporte ────────────────────────────────────────────
    {
      id: "interaction_type",
      label: "Tipo de interacción en vivo",
      type: "enum",
      path: "specific_details.interaction_type",
      owner: "offer",
      options: [
        { value: LiveInteractionType.NONE, label: "Sin encuentros en vivo (100% grabado)" },
        { value: LiveInteractionType.GROUP_Q_AND_A, label: "Q&A grupal en vivo (dudas semanales)" },
        {
          value: LiveInteractionType.ONE_ON_ONE_CHECKINS,
          label: "Check-ins 1:1 con el instructor",
        },
        {
          value: LiveInteractionType.HOT_SEATS,
          label: "Hot seats grupales (casos de alumnos en vivo)",
        },
        {
          value: LiveInteractionType.WORKSHOPS,
          label: "Workshops prácticos (se hace durante la sesión)",
        },
      ],
      hint: "100% grabado = máxima escala, mínimo compromiso del coach. 1:1 y workshops = alta transformación, requiere tu tiempo. Híbrido (grabado + Q&A semanal) es el sweet spot para ticket medio-alto.",
    },
    {
      id: "live_schedule_description",
      label: "Cuándo son los encuentros en vivo",
      type: "text",
      path: "specific_details.live_schedule_description",
      owner: "offer",
      placeholder: "Martes 19:00 (GMT-5) — Q&A grupal de 90 min",
      hint: "Descripción legible del horario. Si se repite semanalmente, indícalo. Esencial para que el alumno evalúe si encaja en su semana antes de comprar.",
    },

    // ─── Compromiso del alumno ────────────────────────────────────────────
    {
      id: "prerequisites_text",
      label: "Conocimientos previos o requisitos",
      type: "textarea",
      path: "specific_details.prerequisites_text",
      owner: "offer",
      rows: 3,
      placeholder:
        "Ideal si ya tienes:\n• Experiencia básica con Meta Ads (al menos 1 campaña lanzada)\n• Cuenta de negocio verificada\n• Presupuesto mínimo de USD 300/mes para ejercicios prácticos",
      hint: "Con qué debe llegar el alumno para aprovechar el programa. Vacío = sin prerrequisitos. Filtra expectativas: 'para principiantes absolutos' vs 'para emprendedores con facturación ≥ USD 5k/mes' son dos posicionamientos distintos.",
    },
    {
      id: "is_application_required",
      label: "¿Requiere aplicación previa?",
      type: "boolean",
      path: "specific_details.is_application_required",
      owner: "offer",
      hint: "Solo los que llenan formulario de aplicación + entrevista acceden al programa. Genera exclusividad y filtra leads no calificados. Típico en masterminds, bootcamps premium y programas 1:1.",
    },
    {
      id: "homework_submission_required",
      label: "¿Hay tareas entregables?",
      type: "boolean",
      path: "specific_details.homework_submission_required",
      owner: "offer",
      hint: "Si los alumnos deben entregar tareas revisadas por ti o el equipo. Aumenta transformación real (hacen lo que aprenden) pero también workload tuyo. Considera delegación a TAs si la cohorte supera 30 personas.",
    },

    // ─── Certificación ────────────────────────────────────────────────────
    {
      id: "has_certification",
      label: "¿Certificado al completar?",
      type: "boolean",
      path: "specific_details.has_certification",
      owner: "offer",
      hint: "Certificado verificable (con QR o link público) eleva valor percibido, sobre todo para profesionales que lo suman a LinkedIn. Alianza con universidad o colegio profesional lo potencia.",
    },

    // ─── Plataforma + comunidad ───────────────────────────────────────────
    {
      id: "community_platform",
      label: "Plataforma de comunidad",
      type: "enum",
      path: "specific_details.community_platform",
      owner: "offer",
      options: [
        { value: CommunityPlatform.NONE, label: "Sin comunidad" },
        {
          value: CommunityPlatform.WHATSAPP,
          label: "WhatsApp grupal (alta adopción Latam, bajo costo)",
        },
        {
          value: CommunityPlatform.TELEGRAM,
          label: "Telegram (grupos grandes, canales broadcast)",
        },
        {
          value: CommunityPlatform.DISCORD,
          label: "Discord (audiencia tech, comunidades gaming/crypto)",
        },
        { value: CommunityPlatform.CIRCLE, label: "Circle (profesional, con curso integrado)" },
        { value: CommunityPlatform.SKOOL, label: "Skool (gamificada + cursos)" },
        { value: CommunityPlatform.SLACK, label: "Slack (B2B, más formal)" },
        {
          value: CommunityPlatform.FACEBOOK_GROUP,
          label: "Grupo de Facebook (legacy, audiencia 35+)",
        },
      ],
      hint: "WhatsApp es lo más adoptado Latam pero no escala más allá de 256 miembros. Circle/Skool son más profesionales pero el alumno debe aprender una app nueva.",
    },
    {
      id: "community_invite_link",
      label: "Link de invitación a la comunidad",
      type: "url",
      path: "specific_details.community_invite_link",
      owner: "offer",
      placeholder: "https://chat.whatsapp.com/... / https://t.me/+... / https://discord.gg/...",
      hint: "Se envía post-checkout al nuevo alumno. Deja vacío si invitas manualmente uno-a-uno. Valida que el link no caducó antes de la cohorte.",
    },
    {
      id: "lms_url",
      label: "URL del aula / LMS",
      type: "url",
      path: "specific_details.lms_url",
      owner: "offer",
      placeholder: "https://tu-academia.hotmart.com / https://tu.kajabi.com",
      hint: "Dónde está alojado el curso. Hotmart/Eduzz/Kiwify dominan Brasil. Teachable/Kajabi/Podia en hispano. Plataforma propia si tienes tech. Se envía post-checkout junto con las credenciales de acceso.",
    },

    // ─── Cohorte específica (edition-level) ───────────────────────────────
    {
      id: "start_date",
      label: "Inicio de esta cohorte",
      type: "text",
      path: "start_date",
      owner: "edition",
      placeholder: "2026-05-01T00:00:00Z",
      hint: "ISO 8601 UTC. Obligatorio para publicar la cohorte. En el landing se muestra en zona horaria del visitante.",
    },
    {
      id: "end_date",
      label: "Fin de esta cohorte",
      type: "text",
      path: "end_date",
      owner: "edition",
      placeholder: "2026-07-31T00:00:00Z",
      hint: "ISO 8601 UTC. Calculá: inicio + duration_weeks semanas. Si el programa tiene semanas de break entre módulos, ajustá.",
    },
    {
      id: "capacity",
      label: "Capacidad máxima (esta cohorte)",
      type: "number",
      path: "capacity",
      owner: "edition",
      placeholder: "50",
      hint: "Cupos máximos. Vacío = sin límite. Escasez real + countdown de cupos restantes convierten mejor que 'quedan pocos' vago.",
    },
    {
      id: "schedule",
      label: "Agenda de sesiones en vivo (esta cohorte)",
      type: "array",
      path: "schedule",
      owner: "edition",
      hint: "Cohortes distintas pueden meetear en días distintos con el mismo currículo. Carga las sesiones recurrentes (día + hora + duración).",
      itemSchema: {
        description: "Una sesión recurrente en la cohorte.",
        fields: [
          {
            id: "title",
            label: "Título de la sesión",
            type: "text",
            path: "title",
            required: true,
            placeholder: "Q&A grupal semanal",
          },
          {
            id: "day_of_week",
            label: "Día",
            type: "text",
            path: "day_of_week",
            placeholder: "Martes",
          },
          {
            id: "time",
            label: "Hora (con zona horaria)",
            type: "text",
            path: "time",
            placeholder: "19:00 GMT-5",
          },
          {
            id: "duration_minutes",
            label: "Duración (minutos)",
            type: "number",
            path: "duration_minutes",
            placeholder: "90",
          },
        ],
      },
    },
  ],
};
