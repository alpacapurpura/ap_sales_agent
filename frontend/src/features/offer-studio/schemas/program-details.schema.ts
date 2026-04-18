import { CommunityPlatform, LiveInteractionType, ProgramStructure } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * PROGRAMA archetype details — curriculum + cohort structure.
 *
 * MIXED scope: the curriculum + structure + community platform are offer-
 * wide (every cohort runs the same program), but start/end dates +
 * cohort_limit + current_enrollment live on the specific LaunchEdition.
 *
 * The cohort-specific schedule array is edition-owned because different
 * cohorts can meet on different days (same curriculum, different calendar).
 */
export const offerProgramDetailsSchema: SectionSchema = {
  key: "offer.program_details",
  title: "Detalles del programa",
  description: "Estructura del programa y ajustes por cohorte.",
  scope: "mixed",
  fields: [
    {
      id: "structure_type",
      label: "Estructura del programa",
      type: "enum",
      path: "specific_details.structure_type",
      owner: "offer",
      options: [
        { value: ProgramStructure.FIXED_COHORT, label: "Cohorte con fechas fijas" },
        { value: ProgramStructure.ROLLING_ADMISSION, label: "Admisión continua" },
        { value: ProgramStructure.CHALLENGE, label: "Challenge intensivo" },
        { value: ProgramStructure.MEMBERSHIP, label: "Membresía recurrente" },
      ],
    },
    {
      id: "duration_weeks",
      label: "Duración (semanas)",
      type: "number",
      path: "specific_details.duration_weeks",
      owner: "offer",
    },
    {
      id: "curriculum",
      label: "Currículo por módulo",
      type: "array",
      path: "specific_details.curriculum",
      owner: "offer",
      hint: "Módulos en orden. Cada módulo con título + descripción + tópicos cubiertos.",
      itemSchema: {
        description: "Un módulo del programa.",
        fields: [
          { id: "title", label: "Título", type: "text", path: "title", required: true },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
          },
          {
            id: "topics",
            label: "Tópicos (uno por línea)",
            type: "textarea",
            path: "topics",
            rows: 3,
          },
        ],
      },
    },
    {
      id: "interaction_type",
      label: "Tipo de interacción",
      type: "enum",
      path: "specific_details.interaction_type",
      owner: "offer",
      options: [
        { value: LiveInteractionType.NONE, label: "Sin interacción en vivo" },
        { value: LiveInteractionType.GROUP_Q_AND_A, label: "Q&A grupal" },
        { value: LiveInteractionType.ONE_ON_ONE_CHECKINS, label: "Check-ins 1:1" },
        { value: LiveInteractionType.HOT_SEATS, label: "Hot seats" },
        { value: LiveInteractionType.WORKSHOPS, label: "Workshops" },
      ],
    },
    {
      id: "community_platform",
      label: "Plataforma de comunidad",
      type: "enum",
      path: "specific_details.community_platform",
      owner: "offer",
      options: [
        { value: CommunityPlatform.NONE, label: "Sin comunidad" },
        { value: CommunityPlatform.CIRCLE, label: "Circle" },
        { value: CommunityPlatform.SKOOL, label: "Skool" },
        { value: CommunityPlatform.DISCORD, label: "Discord" },
        { value: CommunityPlatform.SLACK, label: "Slack" },
        { value: CommunityPlatform.WHATSAPP, label: "WhatsApp" },
        { value: CommunityPlatform.TELEGRAM, label: "Telegram" },
      ],
    },
    {
      id: "has_certification",
      label: "¿Certificación al completar?",
      type: "boolean",
      path: "specific_details.has_certification",
      owner: "offer",
    },
    {
      id: "start_date",
      label: "Inicio de la cohorte",
      type: "text",
      path: "start_date",
      owner: "edition",
      placeholder: "2026-05-01T00:00:00Z",
      hint: "ISO 8601 UTC. Requerido para publicar la cohorte.",
    },
    {
      id: "end_date",
      label: "Fin de la cohorte",
      type: "text",
      path: "end_date",
      owner: "edition",
      placeholder: "2026-07-31T00:00:00Z",
    },
    {
      id: "capacity",
      label: "Capacidad máxima",
      type: "number",
      path: "capacity",
      owner: "edition",
      hint: "Cupos máximos para esta cohorte. Vacío = sin límite.",
    },
    {
      id: "schedule",
      label: "Agenda de sesiones (esta cohorte)",
      type: "array",
      path: "schedule",
      owner: "edition",
      hint: "Horario concreto de esta cohorte. Distinto al de otras cohortes del mismo programa.",
      itemSchema: {
        description: "Una sesión recurrente.",
        fields: [
          { id: "title", label: "Título", type: "text", path: "title", required: true },
          { id: "day_of_week", label: "Día", type: "text", path: "day_of_week" },
          { id: "time", label: "Hora", type: "text", path: "time" },
          {
            id: "duration_minutes",
            label: "Duración (min)",
            type: "number",
            path: "duration_minutes",
          },
        ],
      },
    },
  ],
};
