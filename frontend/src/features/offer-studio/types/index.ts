// --- ENUMS ---
export enum OfferValueLevel {
  N0 = "level_0_free",
  N1 = "level_1_low_ticket",
  N2 = "level_2_mid_ticket",
  N3 = "level_3_high_ticket",
  N4 = "level_4_recurring",
  N5 = "level_5_ultra_high",
  N6 = "level_6_corporate",
}

export enum OfferArchetype {
  PRODUCTO = "producto",
  PROGRAMA = "programa",
  SERVICIO = "servicio",
  MEMBRESIA = "membresia",
  EXPERIENCIA = "experiencia",
}

export enum OfferDeliveryModel {
  DIY = "diy",
  DWY = "dwy",
  DFY = "dfy",
  HYBRID = "hybrid",
}

export enum OfferType {
  FREE_RESOURCE = "free_resource",
  COMMUNITY_LITE = "community_lite",
  CONTENT_ASSET_PODCAST = "content_asset_podcast",
  FREE_WEBINAR_CHALLENGE = "free_webinar_challenge",
  TRIPWIRE_OFFER = "tripwire_offer",
  SELF_PACED_COURSE = "self_paced_course",
  PAID_NEWSLETTER_SUBSCRIPTION = "paid_newsletter_subscription",
  PHYSICAL_MERCH = "physical_merch",
  HYBRID_MENTORSHIP = "hybrid_mentorship",
  COHORT_BASED_COURSE = "cohort_based_course",
  GROUP_COACHING_PROGRAM = "group_coaching_program",
  VIP_DAY_STRATEGY = "vip_day_strategy",
  ONE_ON_ONE_PRIVATE_MENTORING = "one_on_one_private_mentoring",
  DEEP_DIVE_AUDIT = "deep_dive_audit",
  PRODUCTIZED_SERVICE = "productized_service",
  ECOMMERCE_DEVELOPMENT = "ecommerce_development",
  MONTHLY_RETAINER = "monthly_retainer",
  PERFORMANCE_REV_SHARE = "performance_rev_share",
  MASTERMIND_NETWORK = "mastermind_network",
  LUXURY_RETREAT = "luxury_retreat",
  CORPORATE_TRAINING = "corporate_training",
  BRAND_SPONSORSHIP = "brand_sponsorship",
  KEYNOTE_SPEAKING = "keynote_speaking",
}

export enum OfferStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  PAUSED = "paused",
  ARCHIVED = "archived",
  WAITLIST = "waitlist",
  SOLD_OUT = "sold_out",
}

export enum GuaranteeType {
  NONE = "none",
  CONDITIONAL_ACTION_BASED = "conditional_action_based",
  UNCONDITIONAL_30_DAY = "unconditional_30_day",
  DOUBLE_MONEY_BACK = "double_money_back",
  SATISFACTION_OR_FREE_WORK = "satisfaction_or_free_work"
}

export enum DeliverableFormat {
  PDF = "pdf",
  VIDEO = "video",
  AUDIO = "audio",
  LIVE_SESSION = "live_session",
  TEMPLATE = "template",
  COMMUNITY_ACCESS = "community_access",
  SOFTWARE_ACCESS = "software_access",
  PHYSICAL_ITEM = "physical_item",
  SERVICE_HOURS = "service_hours"
}

export enum FinancialCapacity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  ULTRA_HIGH = "ultra_high"
}

export enum OnboardingMechanism {
  INSTANT_ACCESS_EMAIL = "instant_access_email",
  BOOK_KICKOFF_CALL = "book_kickoff_call",
  FILL_INTAKE_FORM = "fill_intake_form",
  JOIN_COMMUNITY = "join_community"
}

export enum FulfillmentType {
  DIGITAL_DOWNLOAD = "digital_download",
  LMS_ACCESS = "lms_access",
  PHYSICAL_SHIPPING = "physical_shipping",
  MANUAL_PROVISIONING = "manual_provisioning"
}

export enum DigitalFormat {
  PDF_EBOOK = "pdf_ebook",
  VIDEO_COURSE = "video_course",
  AUDIO_SERIES = "audio_series",
  NOTION_TEMPLATE = "notion_template",
  SOFTWARE_SAAS = "software_access",
  PHYSICAL_ITEM = "physical_item"
}

export enum ProgramStructure {
  FIXED_COHORT = "fixed_cohort",
  ROLLING_ADMISSION = "rolling_admission",
  CHALLENGE = "challenge",
  MEMBERSHIP = "membership"
}

export enum LiveInteractionType {
  NONE = "none",
  GROUP_Q_AND_A = "group_q_and_a",
  ONE_ON_ONE_CHECKINS = "one_on_one_checkins",
  HOT_SEATS = "hot_seats",
  WORKSHOPS = "workshops"
}

export enum CommunityPlatform {
  NONE = "none",
  WHATSAPP = "whatsapp",
  TELEGRAM = "telegram",
  DISCORD = "discord",
  SKOOL = "skool",
  CIRCLE = "circle",
  FACEBOOK_GROUP = "facebook_group",
  SLACK = "slack"
}

export enum ServiceCategory {
  ADVISORY = "advisory",
  AGENCY = "agency",
  AUTHORITY = "authority"
}

export enum InteractionMode {
  SYNC = "sync",
  ASYNC = "async",
  HYBRID = "hybrid"
}

export enum ServiceFrequency {
  ONE_OFF = "one_off",
  RETAINER = "retainer"
}

export enum EventLocationType {
  VIRTUAL = "virtual",
  PHYSICAL_LOCAL = "physical_local",
  DESTINATION_RETREAT = "destination_retreat"
}

export enum AccommodationType {
  NOT_INCLUDED = "not_included",
  SHARED_ROOM = "shared_room",
  PRIVATE_ROOM = "private_room",
  LUXURY_SUITE = "luxury_suite"
}

export enum PaymentPlanType {
  ONE_TIME = "one_time",
  SUBSCRIPTION = "subscription",
  PAYMENT_PLAN = "payment_plan"
}

export enum AccessDuration {
  LIFETIME = "lifetime",
  LIMITED_TIME = "limited_time",
  SUBSCRIPTION_ACTIVE = "subscription_active"
}

export enum PrerequisiteType {
  NONE = "none",
  APPLICATION_APPROVED = "application_approved",
  PRIOR_PROGRAM_COMPLETION = "prior_program_completion",
  INCOME_LEVEL = "income_level"
}

export enum BillingFrequency {
  MONTHLY = "monthly",
  QUARTERLY = "quarterly",
  ANNUAL = "annual",
  ONE_OFF = "one_off"
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

// --- INTERFACES ---
export interface PricingStructure {
  label: string;
  plan_type?: string;
  total_amount: number;
  currency?: string;
  deposit_required?: number;
  number_of_installments?: number;
  installment_amount?: number;
}

export interface MarketingAsset {
  id: string;
  name: string;
  type: string;
  size?: string;
  url?: string;
}

export interface OfferAsset {
  id?: string;
  type: AssetType;
  name: string;
  url: string;
  size?: string;
  trigger_context?: string;
  is_knowledge_base?: boolean;
}

export interface Offer {
  id: string;
  name: string;
  public_name?: string;
  internal_sku?: string;
  type: OfferType;

  // Archetype system
  archetype?: OfferArchetype;
  format_hint?: string;
  is_lead_magnet?: boolean;
  shows_as_lead_magnet?: boolean;

  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  status: OfferStatus;

  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;

  pricing?: PricingStructure[];
  currency?: string;

  // Polymorphic details
  specific_details?: Record<string, any>;

  // Stats & Metadata
  active_clients?: number; // From specific_details or computed
  metadata_info?: Record<string, any>;

  avatar_id?: string;

  // Marketing Psychology
  marketing_pain_points?: string[];
  marketing_desires?: string[];
  objections?: ObjectionItem[];

  // Deliverables
  deliverables?: DeliverableItem[];

  // Assets (Media/Docs for AI agent)
  assets?: OfferAsset[];

  // Additional Fields
  target_avatar_match?: string[];
  prerequisites?: any[]; // Using any[] for now to match schema flexibility
  includes_offers?: string[];

  guarantee_type?: GuaranteeType;
  guarantee_terms?: string;
  access_duration?: string;
  access_duration_text?: string;
  support_duration_days?: number;
  instructors?: string[];

  onboarding_action?: OnboardingMechanism;
  onboarding_url?: string;
  calendar_type_id?: string;
  checkout_page_url?: string;
  vsl_link?: string;

  landing_page_config?: {
      is_published: boolean;
      slug: string;
      [key: string]: any;
  };
}

export interface DeliverableItem {
  name: string;
  format: string; // Should match DeliverableFormat enum values
  quantity: string;
  value_stack_price: number;
}

export interface AvatarDefinition {
    icp_description?: string;
    anti_avatar?: string;
    voice_tone_config?: Record<string, any>;
    pain_points?: string[];
    desires?: string[];
    awareness_level?: string;
    sophistication_level?: string;
}

export interface ObjectionItem {
  id?: string;
  type: string;  // "price" | "time" | "trust" | "partner" | "custom"
  trigger_phrases: string[];
  strategy: string;
  rebuttal: string;
}

/** @deprecated Use ObjectionItem instead */
export type Objection = ObjectionItem;
