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
  FinancialCapacity
} from ".";

const emptyStringToNull = (val: unknown) => {
  if (val === "" || val === null || val === undefined) return null;
  if (typeof val === "string" && val.trim() === "") return null;
  return val;
};

// Robust schema for dates that handles empty strings from forms
const nullableDateSchema = z.union([z.string().datetime(), z.literal("")])
  .optional()
  .nullable()
  .transform(val => (val === "" ? null : val));

// --- Details Schemas ---

export const ProductDetailsSchema = z.object({
  fulfillment_type: z.nativeEnum(FulfillmentType).optional().nullable(),
  access_url: z.string().url().optional().nullable(),
  access_instructions: z.string().optional().nullable(),
  format: z.nativeEnum(DigitalFormat).optional().nullable(),
  is_downloadable: z.boolean().default(true),
  estimated_consumption_time_minutes: z.number().optional().nullable(),
  requires_shipping: z.boolean().default(false),
  sku_inventory_code: z.string().optional().nullable(),
  stock_quantity: z.number().optional().nullable(),
  shipping_weight_grams: z.number().optional().nullable()
});

export const ServiceDetailsSchema = z.object({
  category: z.nativeEnum(ServiceCategory).optional().nullable(),
  interaction_mode: z.nativeEnum(InteractionMode).optional().nullable(),
  frequency_type: z.nativeEnum(ServiceFrequency).optional().nullable(),
  deliverables_list: z.array(z.string()).default([]),
  revision_rounds: z.number().default(0),
  booking_url: z.string().url().optional().nullable(),
  session_duration_minutes: z.number().optional().nullable(),
  total_sessions_count: z.number().optional().nullable(),
  turnaround_time_days: z.number().optional().nullable(),
  onboarding_brief_url: z.string().url().optional().nullable(),
  min_contract_months: z.number().optional().nullable(),
  audience_reach_metric: z.string().optional().nullable(),
  technical_requirements: z.string().optional().nullable(),
  usage_rights_description: z.string().optional().nullable(),
  requires_contract_signature: z.boolean().default(false)
});

const SessionDetailsSchema = z.object({
  title: z.string(),
  day_of_week: z.string(),
  time: z.string(),
  duration_minutes: z.number().default(60)
});

const ProgramModuleSchema = z.object({
  title: z.string().min(1, "El título es obligatorio"),
  description: z.string().optional().nullable(),
  topics: z.array(z.string()).default([])
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
  homework_submission_required: z.boolean().default(false)
});

export const SubscriptionDetailsSchema = z.object({
  billing_cycle: z.nativeEnum(BillingFrequency).optional().nullable(),
  trial_period_days: z.number().default(0),
  tier_name: z.string().optional().nullable(),
  platform_name: z.string().optional().nullable(),
  cancellation_policy: z.string().optional().nullable(),
  content_update_freq: z.string().optional().nullable(),
  expert_guests: z.boolean().default(false),
  networking_events: z.boolean().default(false)
});

export const EventDetailsSchema = z.object({
  start_date: nullableDateSchema,
  end_date: nullableDateSchema,
  timezone: z.string().default("UTC"),
  location_type: z.nativeEnum(EventLocationType).optional().nullable(),
  virtual_meeting_url: z.string().url().optional().nullable(),
  is_recorded: z.boolean().default(true),
  venue_name: z.string().optional().nullable(),
  venue_address: z.string().optional().nullable(),
  map_link: z.string().url().optional().nullable(),
  accommodation_type: z.nativeEnum(AccommodationType).default(AccommodationType.NOT_INCLUDED),
  recommended_airport_code: z.string().optional().nullable(),
  is_transfer_included: z.boolean().default(false),
  agenda_highlights: z.array(z.string()).default([]),
  dress_code: z.string().optional().nullable(),
  dietary_restrictions_form_url: z.string().url().optional().nullable()
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
  cta_text: z.string().optional().nullable()
});

export const DeliverableItemSchema = z.object({
  name: z.string(),
  format: z.nativeEnum(DeliverableFormat),
  quantity: z.string(),
  value_stack_price: z.number()
});

export const ObjectionItemSchema = z.object({
  id: z.string().optional(),
  type: z.string().min(1, "Tipo es obligatorio"),
  trigger_phrases: z.array(z.string()).default([]),
  strategy: z.string().default(""),
  rebuttal: z.string().default("")
});

export const OfferAssetSchema = z.object({
  id: z.string().optional(),
  type: z.nativeEnum(AssetType),
  name: z.string(),
  url: z.string().url(),
  size: z.string().optional(),
  trigger_context: z.string().optional(),
  is_knowledge_base: z.boolean().default(false)
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
  
  specific_details: z.record(z.string(), z.any()).optional().nullable()
});

export type OfferFormValues = z.infer<typeof OfferSchema>;
