import { z } from "zod";

import {
  OfferArchetype,
  OfferValueLevel,
  OfferDeliveryModel,
  OfferStatus,
  GuaranteeType,
  DeliverableFormat,
  FulfillmentType,
  DigitalFormat,
  ProgramStructure,
  LiveInteractionType,
  CommunityPlatform,
  ServiceCategory,
  InteractionMode,
  ServiceFrequency,
  EventLocationType,
  AccommodationType,
  PaymentPlanType,
  AccessDuration,
  PrerequisiteType,
  OnboardingMechanism,
  BillingFrequency,
  AvatarPersona,
  AssetType,
  FinancialCapacity,
} from ".";

const emptyStringToNull = (val: unknown) => {
  if (val === "" || val === null || val === undefined) return null;
  if (typeof val === "string" && val.trim() === "") return null;
  return val;
};

// Robust schema for dates that handles empty strings from forms
const nullableDateSchema = z
  .union([z.string().datetime(), z.literal("")])
  .optional()
  .nullable()
  .transform((val) => (val === "" ? null : val));

// --- Details Schemas ---

export const ProductDetailsSchema = z.object({
  fulfillment_type: z.nativeEnum(FulfillmentType).optional().nullable(),
  access_url: z.string().url().optional().nullable(),
  access_instructions: z.string().optional().nullable(),
  format: z.nativeEnum(DigitalFormat).optional().nullable(),
  is_downloadable: z.boolean().default(true),
  estimated_consumption_time_minutes: z.number().optional().nullable(),
  /** Preview / sample — sube conversión 30-50% en ebooks y cursos. */
  sample_preview_url: z.string().url().optional().nullable(),
  requires_shipping: z.boolean().default(false),
  sku_inventory_code: z.string().optional().nullable(),
  stock_quantity: z.number().optional().nullable(),
  shipping_weight_grams: z.number().optional().nullable(),
  /** Uno por línea. Carriers Latam realmente usados por el merchant. */
  shipping_carriers_accepted: z.string().optional().nullable(),
  /** Formato libre multi-línea por región (Capital / Interior / Internacional). */
  shipping_estimate_by_region: z.string().optional().nullable(),
  /** Unboxing experience — relevante en cosmética/regalo/artesanía. */
  packaging_description: z.string().optional().nullable(),
  /** Días de devolución — mínimo legal por país + buffer. */
  return_policy_days: z.number().optional().nullable(),
});

/**
 * Canal principal de comunicación para servicios recurrentes o con
 * seguimiento. WhatsApp Business es dominante B2B en Latam — el sales
 * agent menciona este valor al cerrar para alinear expectativa post-venta.
 */
export const ServiceCommunicationChannel = [
  "whatsapp_business",
  "email",
  "slack_shared",
  "telegram",
  "platform_internal",
] as const;
export type ServiceCommunicationChannel = (typeof ServiceCommunicationChannel)[number];

export const ServiceDetailsSchema = z.object({
  category: z.nativeEnum(ServiceCategory).optional().nullable(),
  interaction_mode: z.nativeEnum(InteractionMode).optional().nullable(),
  frequency_type: z.nativeEnum(ServiceFrequency).optional().nullable(),
  deliverables_list: z.array(z.string()).default([]),
  /**
   * Scope-out explícito. Campo decisivo para prevenir scope creep y
   * disputas post-venta en servicios Latam (D-service-1).
   */
  scope_excluded: z.string().optional().nullable(),
  revision_rounds: z.number().default(0),
  booking_url: z.string().url().optional().nullable(),
  session_duration_minutes: z.number().optional().nullable(),
  total_sessions_count: z.number().optional().nullable(),
  turnaround_time_days: z.number().optional().nullable(),
  /** SLA de respuesta a mensajes del cliente en horas hábiles. */
  response_time_hours: z.number().optional().nullable(),
  onboarding_brief_url: z.string().url().optional().nullable(),
  min_contract_months: z.number().optional().nullable(),
  /** Canal principal de comunicación con el cliente. Sales-agent lo menciona al cerrar. */
  primary_communication_channel: z.enum(ServiceCommunicationChannel).optional().nullable(),
  audience_reach_metric: z.string().optional().nullable(),
  technical_requirements: z.string().optional().nullable(),
  usage_rights_description: z.string().optional().nullable(),
  requires_contract_signature: z.boolean().default(false),
});

const SessionDetailsSchema = z.object({
  title: z.string(),
  day_of_week: z.string(),
  time: z.string(),
  duration_minutes: z.number().default(60),
});

const ProgramModuleSchema = z.object({
  title: z.string().min(1, "El título es obligatorio"),
  description: z.string().optional().nullable(),
  topics: z.array(z.string()).default([]),
});

export const ProgramDetailsSchema = z.object({
  curriculum: z.array(ProgramModuleSchema).default([]),
  structure_type: z.nativeEnum(ProgramStructure).optional().nullable(),
  start_date: nullableDateSchema,
  registration_end_date: nullableDateSchema,
  end_date: nullableDateSchema,
  is_end_date_estimated: z.boolean().default(false),
  timezone: z.string().default("UTC"),
  duration_weeks: z.number().optional().nullable(),
  /** Horas/semana de compromiso esperado — pregunta #1 del prospecto. */
  weekly_time_commitment_hours: z.number().optional().nullable(),
  /** Prerrequisitos narrativos (reemplaza el enum legacy). */
  prerequisites_text: z.string().optional().nullable(),
  cohort_limit: z.number().optional().nullable(),
  current_enrollment_count: z.number().default(0),
  is_application_required: z.boolean().default(false),
  interaction_type: z.nativeEnum(LiveInteractionType).optional().nullable(),
  live_schedule_description: z.string().optional().nullable(),
  schedule: z.array(SessionDetailsSchema).default([]),
  lms_url: z.string().url().optional().nullable(),
  community_platform: z.nativeEnum(CommunityPlatform).default(CommunityPlatform.NONE),
  community_invite_link: z.string().url().optional().nullable(),
  has_certification: z.boolean().default(false),
  homework_submission_required: z.boolean().default(false),
});

/** Frecuencia declarada con la que se agrega contenido nuevo. */
export const ContentUpdateFrequency = [
  "weekly",
  "biweekly",
  "monthly",
  "quarterly",
  "on_demand",
  "static_library",
] as const;
export type ContentUpdateFrequency = (typeof ContentUpdateFrequency)[number];

export const SubscriptionDetailsSchema = z.object({
  billing_cycle: z.nativeEnum(BillingFrequency).optional().nullable(),
  billing_frequency: z.nativeEnum(BillingFrequency).optional().nullable(),
  trial_period_days: z.number().default(0),
  tier_name: z.string().optional().nullable(),
  platform_name: z.string().optional().nullable(),
  member_benefits: z.string().optional().nullable(),
  content_update_frequency: z.enum(ContentUpdateFrequency).optional().nullable(),
  /** @deprecated Usá ``content_update_frequency``. */
  content_update_freq: z.string().optional().nullable(),
  cancellation_policy: z.string().optional().nullable(),
  /** Días de anticipación que el miembro debe avisar para no renovar. */
  cancellation_anticipation_days: z.number().optional().nullable(),
  /** Latam legal — aviso previo antes de debitar renovación (MX/AR/PE). */
  auto_renewal_with_notice_days: z.number().optional().nullable(),
  /** Recupera churn involuntario por tarjetas rebotadas. */
  grace_period_days_on_failed_payment: z.number().optional().nullable(),
  onboarding_flow: z.string().optional().nullable(),
  expert_guests: z.boolean().default(false),
  networking_events: z.boolean().default(false),
});

/** Granularidad de comidas incluidas en un evento presencial. */
export const MealsIncludedLevel = [
  "none",
  "coffee_breaks",
  "lunch_only",
  "full_pension",
  "all_inclusive",
] as const;
export type MealsIncludedLevel = (typeof MealsIncludedLevel)[number];

/** Idioma declarado del evento, con opciones de traducción simultánea. */
export const EventLanguage = [
  "es",
  "es_with_en_translation",
  "en",
  "en_with_es_translation",
  "pt",
  "bilingual",
] as const;
export type EventLanguage = (typeof EventLanguage)[number];

export const EventDetailsSchema = z.object({
  start_date: nullableDateSchema,
  end_date: nullableDateSchema,
  timezone: z.string().default("UTC"),
  /** Apertura del venue / check-in (hora local del evento). */
  checkin_start_time: z.string().optional().nullable(),
  /** Fecha límite ISO 8601 para confirmación de asistencia. */
  rsvp_deadline: z.string().optional().nullable(),
  location_type: z.nativeEnum(EventLocationType).optional().nullable(),
  virtual_meeting_url: z.string().url().optional().nullable(),
  is_recorded: z.boolean().default(true),
  /** URL de streaming para eventos híbridos presencial + online. */
  live_streamed_secondary_url: z.string().url().optional().nullable(),
  venue_name: z.string().optional().nullable(),
  venue_address: z.string().optional().nullable(),
  map_link: z.string().url().optional().nullable(),
  accommodation_type: z.nativeEnum(AccommodationType).default(AccommodationType.NOT_INCLUDED),
  /** Nivel de comidas incluidas — decisivo en retiros. */
  meals_included: z.enum(MealsIncludedLevel).optional().nullable(),
  recommended_airport_code: z.string().optional().nullable(),
  is_transfer_included: z.boolean().default(false),
  agenda_highlights: z.array(z.string()).default([]),
  /** Uno por línea. Lista de qué traer — evita no-shows o reclamos en retiros. */
  what_to_bring: z.string().optional().nullable(),
  dress_code: z.string().optional().nullable(),
  language_spoken: z.enum(EventLanguage).optional().nullable(),
  /** Si admite acompañantes no-inscritos (pareja, hijos). */
  is_family_friendly: z.boolean().default(false),
  age_restrictions: z.string().optional().nullable(),
  /** Latam legal (AR Ley 26.378, CL Ley 20.422). */
  accessibility_notes: z.string().optional().nullable(),
  /** Días antes del evento con reembolso 100%. */
  refund_deadline_days: z.number().optional().nullable(),
  dietary_restrictions_form_url: z.string().url().optional().nullable(),
});

// --- Shared Schemas ---

export const PricingStructureSchema = z.object({
  label: z.string(),
  plan_type: z.nativeEnum(PaymentPlanType).optional().nullable(),
  total_amount: z.number(),
  // Optional per-option currency override. Omitted = inherit from the
  // offer-level currency / tenant default.
  currency: z.string().optional(),
  deposit_required: z.number().default(0.0),
  number_of_installments: z.number().int().default(1),
  installment_amount: z.number().default(0.0),
  is_default: z.boolean().default(false),
  savings_claim: z.string().optional().nullable(),
  // Membership tier fields
  benefits: z.array(z.string()).default([]),
  is_highlighted: z.boolean().default(false),
  cta_text: z.string().optional().nullable(),
});

export const DeliverableItemSchema = z.object({
  name: z.string(),
  format: z.nativeEnum(DeliverableFormat),
  quantity: z.string(),
  value_stack_price: z.number(),
});

export const ObjectionItemSchema = z.object({
  id: z.string().optional(),
  type: z.string().min(1, "Tipo es obligatorio"),
  trigger_phrases: z.array(z.string()).default([]),
  strategy: z.string().default(""),
  rebuttal: z.string().default(""),
});

export const OfferAssetSchema = z.object({
  id: z.string().optional(),
  type: z.nativeEnum(AssetType),
  name: z.string(),
  url: z.string().url(),
  size: z.string().optional(),
  trigger_context: z.string().optional(),
  is_knowledge_base: z.boolean().default(false),
});

// --- Main Offer Schema ---

export const OfferSchema = z.object({
  id: z.string().uuid().optional(),
  internal_sku: z.string().optional().nullable(),
  public_name: z.string().min(1, "Name is required"),
  archetype: z.nativeEnum(OfferArchetype),
  format_hint: z.string().optional().nullable(),
  is_lead_magnet: z.boolean().default(false),
  // Wizard-driven: will this offer run in editions/cohorts/batches?
  // Backend applies archetype-aware default when omitted.
  has_editions: z.boolean().optional(),
  offer_value_level: z.nativeEnum(OfferValueLevel).optional().nullable(),
  delivery_model: z.nativeEnum(OfferDeliveryModel).optional().nullable(),

  headline_promise: z.string().optional(),
  avatar_id: z.string().uuid().optional().nullable(),
  target_avatar_match: z.array(z.nativeEnum(AvatarPersona)).default([]),
  marketing_pain_points: z.array(z.string()).default([]),
  marketing_desires: z.array(z.string()).default([]),
  objections: z.array(ObjectionItemSchema).default([]),
  primary_outcome: z.string().optional(),
  time_to_value: z.string().optional(),

  access_duration: z.nativeEnum(AccessDuration).optional().nullable(),
  access_duration_text: z.string().optional().nullable(), // For specific text like "1 Year", "6 Months"
  support_duration_days: z.number().optional().nullable(),
  instructors: z.array(z.string()).default([]),

  requires_application: z.boolean().default(false),
  min_financial_capacity: z.nativeEnum(FinancialCapacity).default(FinancialCapacity.LOW),
  prerequisites: z.array(z.union([z.nativeEnum(PrerequisiteType), z.string()])).default([]),
  anti_avatar_keywords: z.array(z.string()).default([]),

  pricing_options: z.array(PricingStructureSchema).default([]),
  price_pay_in_full: z.number().optional().nullable(),
  // Optional — resolved at render time via useTenantLocale() fallback chain.
  currency: z.string().optional(),

  guarantee_type: z.nativeEnum(GuaranteeType).default(GuaranteeType.NONE),
  guarantee_terms: z.string().optional().nullable(),

  downsell_offer_id: z.string().uuid().optional().nullable(),
  upsell_offer_id: z.string().uuid().optional().nullable(),
  includes_offers: z.array(z.string().uuid()).default([]),
  deliverables: z.array(DeliverableItemSchema).default([]),
  assets: z.array(OfferAssetSchema).default([]),

  onboarding_action: z.nativeEnum(OnboardingMechanism).optional().nullable(),
  onboarding_url: z.string().url().optional().nullable(),

  vsl_link: z.string().optional().nullable(),
  checkout_page_url: z.string().optional().nullable(),
  calendar_type_id: z.string().optional().nullable(),

  status: z.nativeEnum(OfferStatus).default(OfferStatus.DRAFT),

  specific_details: z.record(z.string(), z.any()).optional().nullable(),
});

export type OfferFormValues = z.infer<typeof OfferSchema>;
