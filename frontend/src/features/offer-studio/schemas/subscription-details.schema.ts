import { BillingFrequency, CommunityPlatform } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * MEMBRESIA archetype details — facturación recurrente, comunidad,
 * política de cancelación y permanencia.
 *
 * Edition-less por archetype: todos los miembros comparten la misma
 * membresía. No hay variaciones por "cohorte" — si necesitás variantes
 * (Gold/Platinum/Enterprise) usá ``VariantStructure.TIER``.
 *
 * **Latam — decisiones de diseño:**
 * - ``auto_renewal_with_notice_days`` es obligatorio para cumplir con
 *   leyes del consumidor (LFPC México, Ley de Defensa del Consumidor
 *   Argentina, Código de Consumo Perú). Renovar sin aviso previo es
 *   causal de refund forzado por la pasarela.
 * - ``trial_period_days`` ya existía en el zod pero estaba oculto. Es
 *   decisivo en SaaS y comunidades para product-led growth.
 * - ``grace_period_days_on_failed_payment`` es Latam-crítico: las
 *   tarjetas rebotan por límite, por vencimiento o por banco bloqueando
 *   cobros internacionales. Un buen grace period (3-7 días) con reintento
 *   automático recupera el 30-50% de churn involuntario.
 * - ``cancellation_anticipation_days`` comunica expectativa de permanencia
 *   sin imponer penalidad legal. Ej: "cancelá con 7 días de aviso antes
 *   del próximo ciclo" es aceptable; "pagá 3 meses de penalidad" no lo es.
 */
export const offerSubscriptionDetailsSchema: SectionSchema = {
  key: "offer.subscription_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    // ─── Facturación ──────────────────────────────────────────────────────
    {
      id: "billing_frequency",
      label: "Frecuencia de facturación",
      type: "enum",
      path: "specific_details.billing_frequency",
      options: [
        { value: BillingFrequency.MONTHLY, label: "Mensual (típico, churn más alto)" },
        { value: BillingFrequency.QUARTERLY, label: "Trimestral (balance entre cashflow y retención)" },
        { value: BillingFrequency.ANNUAL, label: "Anual con descuento (reduce churn, mejora LTV)" },
      ],
      hint: "Mensual convierte más, anual retiene más. Ofrecer ambos con 15-20% off en anual captura a los dos perfiles. Evaluá también la estacionalidad de tu oferta.",
    },
    {
      id: "tier_name",
      label: "Nombre del plan (si hay varios tiers, el de esta oferta)",
      type: "text",
      path: "specific_details.tier_name",
      placeholder: "Pro / Premium / Club VIP / Gold",
      hint: "Si tu membresía tiene 3 planes (Starter / Pro / Enterprise), cada plan es una oferta con el mismo archetype. Usá este campo para diferenciar. Solo un plan, dejá vacío.",
    },
    {
      id: "trial_period_days",
      label: "Período de prueba gratis (días)",
      type: "number",
      path: "specific_details.trial_period_days",
      placeholder: "14",
      hint: "0 = sin trial. Trial de 7-14 días sube conversión a pago en SaaS y comunidades. ¿Pedís tarjeta para activar el trial? Menos conversión inicial pero más miembros pagos al finalizar.",
    },

    // ─── Valor entregado ──────────────────────────────────────────────────
    {
      id: "member_benefits",
      label: "Qué recibe el miembro",
      type: "textarea",
      path: "specific_details.member_benefits",
      rows: 6,
      placeholder:
        "• Acceso completo a biblioteca con 40+ masterclasses\n• Q&A en vivo mensual con el fundador\n• Comunidad privada en WhatsApp\n• Descuento del 20% en todos nuestros productos\n• Asignación de buddy al ingresar",
      hint: "Uno por línea. Sé ultra específico — el miembro decide seguir pagando cada mes en función de estos beneficios. Incluí frecuencia (mensual / semanal) cuando aplique.",
    },
    {
      id: "content_update_frequency",
      label: "Con qué frecuencia agregás contenido nuevo",
      type: "enum",
      path: "specific_details.content_update_frequency",
      options: [
        { value: "weekly", label: "Semanal (comunidades activas)" },
        { value: "biweekly", label: "Quincenal" },
        { value: "monthly", label: "Mensual (lo más común)" },
        { value: "quarterly", label: "Trimestral (curado)" },
        { value: "on_demand", label: "Solo por demanda / pedidos de miembros" },
        { value: "static_library", label: "Biblioteca estática (no agrego más)" },
      ],
      hint: "La razón #1 de cancelación en membresías Latam es 'no veo contenido nuevo'. Semanal es agotador pero retiene; mensual es lo más sostenible para equipos chicos.",
    },

    // ─── Comunidad ────────────────────────────────────────────────────────
    {
      id: "community_platform",
      label: "Plataforma de comunidad",
      type: "enum",
      path: "specific_details.community_platform",
      options: [
        { value: CommunityPlatform.NONE, label: "Sin comunidad" },
        { value: CommunityPlatform.WHATSAPP, label: "WhatsApp (alta adopción Latam, limita a 256)" },
        { value: CommunityPlatform.TELEGRAM, label: "Telegram (grupos grandes, broadcasts)" },
        { value: CommunityPlatform.DISCORD, label: "Discord (audiencia tech/creator/gaming)" },
        { value: CommunityPlatform.CIRCLE, label: "Circle (más profesional, cursos integrados)" },
        { value: CommunityPlatform.SKOOL, label: "Skool (gamificada, trending)" },
        { value: CommunityPlatform.SLACK, label: "Slack (B2B formal)" },
        { value: CommunityPlatform.FACEBOOK_GROUP, label: "Grupo de Facebook (legacy, audiencia 35+)" },
      ],
      hint: "La plataforma define el feeling y el techo. WhatsApp íntimo pero se satura. Circle/Skool profesional pero curva de aprendizaje. Evaluá dónde pasa tiempo tu avatar.",
    },

    // ─── Política de cancelación + renovación (Latam legal) ───────────────
    {
      id: "cancellation_policy",
      label: "Política de cancelación",
      type: "textarea",
      path: "specific_details.cancellation_policy",
      rows: 4,
      placeholder:
        "Podés cancelar tu membresía en cualquier momento desde tu panel. Mantendrás acceso hasta el final del período facturado. No hay cargos por cancelar y no guardamos tus datos más allá de lo requerido por ley.",
      hint: "Ley del Consumidor Latam (MX, AR, PE, CO) exige cancelación simple. Procesos engorrosos (llamadas obligatorias, formularios) activan disputas en pasarela → chargebacks. Simpleza == menos fricción post-venta.",
    },
    {
      id: "cancellation_anticipation_days",
      label: "Días de anticipación para evitar renovación automática",
      type: "number",
      path: "specific_details.cancellation_anticipation_days",
      placeholder: "7",
      hint: "Cuántos días antes del próximo ciclo debe cancelar el miembro para no ser renovado. 0 = puede cancelar el mismo día. 7 es lo más común. Más de 15 genera fricción y reclamos.",
    },
    {
      id: "auto_renewal_with_notice_days",
      label: "Aviso previo antes de renovar (días)",
      type: "number",
      path: "specific_details.auto_renewal_with_notice_days",
      placeholder: "5",
      hint: "Latam legal: la mayoría de países exigen aviso por email/SMS antes de debitar renovación. 3-7 días es estándar. Sin este aviso la pasarela puede aceptar disputas.",
    },
    {
      id: "grace_period_days_on_failed_payment",
      label: "Período de gracia por pago fallido (días)",
      type: "number",
      path: "specific_details.grace_period_days_on_failed_payment",
      placeholder: "5",
      hint: "Cuando la tarjeta rebota, ¿por cuántos días mantenés el acceso y reintentás el cobro? 3-7 días recuperan 30-50% de churn involuntario (tarjetas vencidas, límite temporal). 0 días = perdés el miembro inmediatamente.",
    },

    // ─── Onboarding del nuevo miembro ─────────────────────────────────────
    {
      id: "onboarding_flow",
      label: "Qué recibe el miembro en las primeras 24-48h",
      type: "textarea",
      path: "specific_details.onboarding_flow",
      rows: 4,
      placeholder:
        "• Email de bienvenida con acceso a la plataforma\n• Invitación automática al grupo de WhatsApp\n• Video de onboarding de 3 min explicando dónde está todo\n• Agenda opcional kickoff call de 20 min con tu buddy",
      hint: "El onboarding decide los primeros 3 meses. Miembros que NO usan el producto en la primera semana tienen 4x más probabilidad de cancelar. Automatizá todo lo posible y personalizá el primer contacto humano.",
    },
  ],
};
