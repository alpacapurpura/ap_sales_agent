// --- ENUMS ---
export enum OfferValueLevel {
  N0 = "N0",
  N1 = "N1",
  N2 = "N2",
  N3 = "N3",
  N4 = "N4",
  N5 = "N5",
  N6 = "N6",
}

export enum OfferDeliveryModel {
  DIY = "DIY",
  DWY = "DWY",
  DFY = "DFY",
  B2B = "B2B",
}

export enum OfferType {
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
  ECOMMERCE_DEVELOPMENT = "ECOMMERCE_DEVELOPMENT",
  MONTHLY_RETAINER = "MONTHLY_RETAINER",
  PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE",
  MASTERMIND_NETWORK = "MASTERMIND_NETWORK",
  LUXURY_RETREAT = "LUXURY_RETREAT",
  CORPORATE_TRAINING = "CORPORATE_TRAINING",
  BRAND_SPONSORSHIP = "BRAND_SPONSORSHIP",
  KEYNOTE_SPEAKING = "KEYNOTE_SPEAKING",
}

export enum OfferStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  PAUSED = "PAUSED",
  ARCHIVED = "ARCHIVED",
  WAITLIST = "WAITLIST",
  SOLD_OUT = "SOLD_OUT",
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

export enum FinancialCapacity {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  ULTRA_HIGH = "ULTRA_HIGH"
}

export enum OnboardingMechanism {
  CHECKOUT_LINK = "SEND_LINK",
  CALENDAR_BOOKING = "BOOK_CALL",
  INTAKE_FORM = "INTAKE_FORM",
  COMMUNITY_INVITE = "JOIN_COMMUNITY"
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

export enum BillingFrequency {
  MONTHLY = "MONTHLY",
  QUARTERLY = "QUARTERLY",
  YEARLY = "YEARLY"
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

  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  status: OfferStatus; // Mapped from backend string to Enum if possible, or just string

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
