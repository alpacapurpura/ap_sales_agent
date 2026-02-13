import { z } from "zod";
import { 
  OfferType, 
  OfferValueLevel, 
  OfferDeliveryModel, 
  OfferStatus 
} from "@/lib/api/offer";

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

export { OfferType, OfferValueLevel, OfferDeliveryModel, OfferStatus };

// --- Enums ---

// OfferType, OfferValueLevel, OfferDeliveryModel, OfferStatus are imported from @/lib/api/offer
// to ensure consistency with the Backend API.

export enum FulfillmentType {
  FREE_RESOURCE = "FREE_RESOURCE",
  COMMUNITY_LITE = "COMMUNITY_LITE",
  CONTENT_ASSET_PODCAST = "CONTENT_ASSET_PODCAST",
  FREE_WEBINAR_CHALLENGE = "FREE_WEBINAR_CHALLENGE",
  TRIPWIRE_OFFER = "TRIPWIRE_OFFER",
  SELF_PACED_COURSE = "SELF_PACED_COURSE",
  PAID_NEWSLETTER_SUBSCRIPTION = "PAID_NEWSLETTER_SUBSCRIPTION",
  PHYSICAL_MERCH = "PHYSICAL_MERCH",
  HYBRID_MENTORSHIP = "HYBRID_MENTORSHIP",
  COHORT_BASED_COURSE = "COHORT_BASED_COURSE",
  GROUP_COACHING_PROGRAM = "GROUP_COACHING_PROGRAM",
  VIP_DAY_STRATEGY = "VIP_DAY_STRATEGY",
  ONE_ON_ONE_PRIVATE_MENTORING = "1ON1_PRIVATE_MENTORING",
  DEEP_DIVE_AUDIT = "DEEP_DIVE_AUDIT",
  PRODUCTIZED_SERVICE = "PRODUCTIZED_SERVICE",
  MONTHLY_RETAINER = "MONTHLY_RETAINER",
  PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE",
  MASTERMIND_NETWORK = "MASTERMIND_NETWORK",
  LUXURY_RETREAT = "LUXURY_RETREAT",
  CORPORATE_TRAINING = "CORPORATE_TRAINING",
  BRAND_SPONSORSHIP = "BRAND_SPONSORSHIP",
  KEYNOTE_SPEAKING = "KEYNOTE_SPEAKING"
}





export enum FulfillmentType {
  DIRECT_DOWNLOAD = "DIRECT_DOWNLOAD",
  EXTERNAL_PLATFORM_ACCESS = "EXTERNAL_PLATFORM",
  PHYSICAL_SHIPPING = "PHYSICAL_SHIPPING"
}

export enum DigitalFormat {
  PDF_DOCUMENT = "PDF",
  VIDEO_FILE = "MP4/MOV",
  AUDIO_FILE = "MP3",
  SPREADSHEET = "XLS/CSV",
  NOTION_TEMPLATE = "NOTION",
  ZIP_BUNDLE = "ZIP",
  SAAS_ACCESS = "SAAS_KEY",
  PHYSICAL_ITEM = "PHYSICAL"
}

export enum ProgramStructure {
  FIXED_DATE_COHORT = "FIXED_COHORT",
  ROLLING_ADMISSION = "ROLLING_EVERGREEN",
  CHALLENGE_SPRINT = "CHALLENGE"
}

export enum LiveInteractionType {
  GROUP_Q_AND_A = "GROUP_Q&A",
  WORKSHOP_PRACTICAL = "WORKSHOP",
  LIVE_PROGRAM_DELIVERY = "LIVE_PROGRAM_DELIVERY",
  HYBRID_SUPPORT = "HYBRID",
  NO_LIVE_COMPONENTS = "ASYNC_ONLY"
}

export enum CommunityPlatform {
  WHATSAPP_TELEGRAM = "CHAT_APP",
  FACEBOOK_GROUP = "FB_GROUP",
  CIRCLE_SKOOL = "DEDICATED_PLATFORM",
  DISCORD_SLACK = "CHAT_SERVER",
  ZOOM = "ZOOM",
  GOOGLE_MEETS = "GOOGLE_MEETS",
  NONE = "NONE"
}

export enum ServiceCategory {
  ADVISORY_CONSULTING = "ADVISORY",
  DONE_FOR_YOU_AGENCY = "EXECUTION_AGENCY",
  B2B_AUTHORITY_RENTAL = "AUTHORITY_RENTAL"
}

export enum InteractionMode {
  SYNCHRONOUS_LIVE = "SYNC_LIVE",
  ASYNC_DELIVERY = "ASYNC_DELIVERY",
  HYBRID_MODEL = "HYBRID"
}

export enum ServiceFrequency {
  ONE_OFF_PROJECT = "ONE_OFF",
  RETAINER_RECURRING = "RETAINER",
  PACK_OF_SESSIONS = "PACK"
}

export enum GuaranteeType {
  UNCONDITIONAL_X_DAY = "UNCONDITIONAL_X_DAY",
  CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED",
  EXCHANGE_ONLY = "EXCHANGE_ONLY",
  NO_REFUNDS = "NO_REFUNDS"
}



export enum DeliverableFormat {
  LIVE_GROUP_CALL = "LIVE_GROUP_CALL",
  ONE_ON_ONE_CALL = "1ON1_CALL",
  RECORDED_CONTENT = "RECORDED_CONTENT",
  PHYSICAL_SHIPMENT = "PHYSICAL_SHIPMENT",
  DFY_ASSET = "DFY_ASSET"
}

export enum EventLocationType {
  VIRTUAL_REMOTE = "VIRTUAL",
  IN_PERSON_LOCAL = "IN_PERSON_LOCAL",
  DESTINATION_RETREAT = "DESTINATION_RETREAT"
}

export enum AccommodationType {
  NOT_INCLUDED = "NOT_INCLUDED",
  SHARED_ROOM = "SHARED_ROOM",
  PRIVATE_ROOM = "PRIVATE_ROOM",
  LUXURY_SUITE = "LUXURY_SUITE"
}

export enum PaymentPlanType {
  PAY_IN_FULL = "PAY_IN_FULL",
  INTERNAL_SPLIT_PAY = "SPLIT_PAY",
  THIRD_PARTY_FINANCE = "3RD_PARTY",
  SUBSCRIPTION_RECURRING = "SUBSCRIPTION"
}

export enum AccessDuration {
  LIFETIME_CONTENT = "LIFETIME",
  LIMITED_TIME_ACCESS = "LIMITED_TIME",
  DURATION_OF_PAYMENT = "PAY_TO_PLAY",
  HYBRID_ACCESS = "HYBRID_ACCESS"
}

export enum PrerequisiteType {
  NO_PREREQUISITE = "NONE",
  GENDER_IDENTITY = "GENDER_IDENTITY",
  REVENUE_LEVEL = "REVENUE_LEVEL",
  BUSINESS_STAGE = "BUSINESS_STAGE"
}

export enum OnboardingMechanism {
  CHECKOUT_LINK = "SEND_LINK",
  CALENDAR_BOOKING = "BOOK_CALL",
  INTAKE_FORM = "INTAKE_FORM",
  COMMUNITY_INVITE = "JOIN_COMMUNITY"
}

export enum BillingFrequency {
  MONTHLY = "MONTHLY",
  QUARTERLY = "QUARTERLY",
  YEARLY = "YEARLY"
}

export enum FinancialCapacity {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  ULTRA_HIGH = "ULTRA_HIGH"
}

export enum AvatarPersona {
  BEGINNER = "BEGINNER",
  INTERMEDIATE = "INTERMEDIATE",
  ADVANCED = "ADVANCED",
  EXPERT = "EXPERT"
}

export enum AssetType {
  IMAGE = "IMAGE",
  VIDEO = "VIDEO",
  AUDIO = "AUDIO",
  PDF = "PDF",
  TXT = "TXT",
  URL = "URL"
}


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
  deposit_required: z.number().default(0.0),
  number_of_installments: z.number().int().default(1),
  installment_amount: z.number().default(0.0),
  is_default: z.boolean().default(false),
  savings_claim: z.string().optional().nullable()
});

export const DeliverableItemSchema = z.object({
  name: z.string(),
  format: z.nativeEnum(DeliverableFormat),
  quantity: z.string(),
  value_stack_price: z.number()
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
  type: z.nativeEnum(OfferType),
  offer_value_level: z.nativeEnum(OfferValueLevel).optional().nullable(),
  delivery_model: z.nativeEnum(OfferDeliveryModel).optional().nullable(),
  
  headline_promise: z.string().optional(),
  avatar_id: z.string().uuid().optional().nullable(),
  target_avatar_match: z.array(z.nativeEnum(AvatarPersona)).default([]),
  marketing_pain_points: z.array(z.string()).default([]),
  marketing_desires: z.array(z.string()).default([]),
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
  currency: z.string().default("USD"),
  
  guarantee_type: z.nativeEnum(GuaranteeType).default(GuaranteeType.NO_REFUNDS),
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
