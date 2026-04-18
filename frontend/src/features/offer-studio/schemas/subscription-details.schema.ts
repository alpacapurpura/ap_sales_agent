import { BillingFrequency, CommunityPlatform } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * MEMBRESIA archetype details — recurring access + community platform.
 *
 * Edition-less archetype: every subscription member inherits the same
 * billing + platform. Per-cohort variations do not exist for memberships.
 */
export const offerSubscriptionDetailsSchema: SectionSchema = {
  key: "offer.subscription_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "billing_frequency",
      label: "Frecuencia de facturación",
      type: "enum",
      path: "specific_details.billing_frequency",
      options: [
        { value: BillingFrequency.MONTHLY, label: "Mensual" },
        { value: BillingFrequency.QUARTERLY, label: "Trimestral" },
        { value: BillingFrequency.ANNUAL, label: "Anual" },
      ],
    },
    {
      id: "community_platform",
      label: "Plataforma de la comunidad",
      type: "enum",
      path: "specific_details.community_platform",
      options: [
        { value: CommunityPlatform.NONE, label: "Sin plataforma" },
        { value: CommunityPlatform.CIRCLE, label: "Circle" },
        { value: CommunityPlatform.SKOOL, label: "Skool" },
        { value: CommunityPlatform.DISCORD, label: "Discord" },
        { value: CommunityPlatform.SLACK, label: "Slack" },
        { value: CommunityPlatform.WHATSAPP, label: "WhatsApp" },
        { value: CommunityPlatform.TELEGRAM, label: "Telegram" },
        { value: CommunityPlatform.FACEBOOK_GROUP, label: "Grupo de Facebook" },
      ],
    },
    {
      id: "member_benefits",
      label: "Beneficios para miembros",
      type: "textarea",
      path: "specific_details.member_benefits",
      rows: 5,
      hint: "Uno por línea. Todo lo que recibe un miembro activo (acceso, llamadas, recursos).",
    },
    {
      id: "cancellation_policy",
      label: "Política de cancelación",
      type: "textarea",
      path: "specific_details.cancellation_policy",
      rows: 3,
      hint: "Cómo y cuándo puede cancelar el miembro.",
    },
    {
      id: "onboarding_flow",
      label: "Onboarding de nuevos miembros",
      type: "textarea",
      path: "specific_details.onboarding_flow",
      rows: 3,
      hint: "Qué recibe el miembro en las primeras 24h / semana.",
    },
  ],
};
