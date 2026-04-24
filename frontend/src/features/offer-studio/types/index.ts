// --- ENUMS ---

/**
 * Sprint 15.1 — canonical variant taxonomy. Mirrors the backend
 * ``VariantStructure`` enum verbatim. Covers every way an offer can
 * fragment into sellable instances, regardless of whether those instances
 * are temporal (cohortes, salidas) or non-temporal (planes, SKUs,
 * modalidades, idiomas, regiones).
 *
 * Vive en types/ (no en api/) para evitar el ciclo types ↔ api.
 *
 * Cambios requieren coordinación con backend —
 * ``variant_structure_catalog.py`` es el SSoT.
 */
export type VariantStructure =
  | "temporal_cohort"
  | "temporal_single_date"
  | "recurring_intake"
  | "tier"
  | "sku_variant"
  | "regional"
  | "modality"
  | "language";

export enum OfferValueLevel {
  LEAD_MAGNET = "lead_magnet",
  ACTIVACION = "activacion",
  TRANSFORMACION = "transformacion",
  MAXIMIZACION = "maximizacion",
  CORPORATIVO = "corporativo",
}

/** Map legacy DB values to new enum values (for adapter backward compat) */
export const LEGACY_VALUE_LEVEL_MAP: Record<string, OfferValueLevel> = {
  level_0_free: OfferValueLevel.LEAD_MAGNET,
  level_1_low_ticket: OfferValueLevel.ACTIVACION,
  level_2_mid_ticket: OfferValueLevel.TRANSFORMACION,
  level_3_high_ticket: OfferValueLevel.TRANSFORMACION,
  level_4_recurring: OfferValueLevel.TRANSFORMACION,
  level_5_ultra_high: OfferValueLevel.MAXIMIZACION,
  level_6_corporate: OfferValueLevel.CORPORATIVO,
};

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

export enum OfferStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  PAUSED = "paused",
  ARCHIVED = "archived",
  WAITLIST = "waitlist",
  SOLD_OUT = "sold_out",
}

export enum EditionStatus {
  DRAFT = "draft",
  UPCOMING = "upcoming",
  ACTIVE = "active",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

export enum EditionVisibility {
  PRIVATE = "private",
  PUBLIC = "public",
}

export enum GuaranteeType {
  NONE = "none",
  CONDITIONAL_ACTION_BASED = "conditional_action_based",
  UNCONDITIONAL_30_DAY = "unconditional_30_day",
  DOUBLE_MONEY_BACK = "double_money_back",
  SATISFACTION_OR_FREE_WORK = "satisfaction_or_free_work",
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
  SERVICE_HOURS = "service_hours",
}

export enum FinancialCapacity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  ULTRA_HIGH = "ultra_high",
}

export enum OnboardingMechanism {
  INSTANT_ACCESS_EMAIL = "instant_access_email",
  BOOK_KICKOFF_CALL = "book_kickoff_call",
  FILL_INTAKE_FORM = "fill_intake_form",
  JOIN_COMMUNITY = "join_community",
}

export enum FulfillmentType {
  DIGITAL_DOWNLOAD = "digital_download",
  LMS_ACCESS = "lms_access",
  PHYSICAL_SHIPPING = "physical_shipping",
  MANUAL_PROVISIONING = "manual_provisioning",
}

export enum DigitalFormat {
  PDF_EBOOK = "pdf_ebook",
  VIDEO_COURSE = "video_course",
  AUDIO_SERIES = "audio_series",
  NOTION_TEMPLATE = "notion_template",
  SOFTWARE_SAAS = "software_access",
  PHYSICAL_ITEM = "physical_item",
}

export enum ProgramStructure {
  FIXED_COHORT = "fixed_cohort",
  ROLLING_ADMISSION = "rolling_admission",
  CHALLENGE = "challenge",
  MEMBERSHIP = "membership",
}

export enum LiveInteractionType {
  NONE = "none",
  GROUP_Q_AND_A = "group_q_and_a",
  ONE_ON_ONE_CHECKINS = "one_on_one_checkins",
  HOT_SEATS = "hot_seats",
  WORKSHOPS = "workshops",
}

export enum CommunityPlatform {
  NONE = "none",
  WHATSAPP = "whatsapp",
  TELEGRAM = "telegram",
  DISCORD = "discord",
  SKOOL = "skool",
  CIRCLE = "circle",
  FACEBOOK_GROUP = "facebook_group",
  SLACK = "slack",
}

export enum ServiceCategory {
  ADVISORY = "advisory",
  AGENCY = "agency",
  AUTHORITY = "authority",
}

export enum InteractionMode {
  SYNC = "sync",
  ASYNC = "async",
  HYBRID = "hybrid",
}

export enum ServiceFrequency {
  ONE_OFF = "one_off",
  RETAINER = "retainer",
}

export enum EventLocationType {
  VIRTUAL = "virtual",
  PHYSICAL_LOCAL = "physical_local",
  DESTINATION_RETREAT = "destination_retreat",
}

export enum AccommodationType {
  NOT_INCLUDED = "not_included",
  SHARED_ROOM = "shared_room",
  PRIVATE_ROOM = "private_room",
  LUXURY_SUITE = "luxury_suite",
}

export enum PaymentPlanType {
  ONE_TIME = "one_time",
  SUBSCRIPTION = "subscription",
  PAYMENT_PLAN = "payment_plan",
}

export enum AccessDuration {
  LIFETIME = "lifetime",
  LIMITED_TIME = "limited_time",
  SUBSCRIPTION_ACTIVE = "subscription_active",
}

export enum PrerequisiteType {
  NONE = "none",
  APPLICATION_APPROVED = "application_approved",
  PRIOR_PROGRAM_COMPLETION = "prior_program_completion",
  INCOME_LEVEL = "income_level",
}

export enum BillingFrequency {
  MONTHLY = "monthly",
  QUARTERLY = "quarterly",
  ANNUAL = "annual",
  ONE_OFF = "one_off",
}

export enum AvatarPersona {
  BEGINNER = "BEGINNER",
  INTERMEDIATE = "INTERMEDIATE",
  ADVANCED = "ADVANCED",
  EXPERT = "EXPERT",
}

export enum AssetType {
  IMAGE = "IMAGE",
  VIDEO = "VIDEO",
  AUDIO = "AUDIO",
  PDF = "PDF",
  TXT = "TXT",
  URL = "URL",
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
  // Membership tier fields
  benefits?: string[];
  is_highlighted?: boolean;
  cta_text?: string;
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
  // Archetype system
  archetype: OfferArchetype;
  format_hint?: string;
  /** 7th SSoT axis link (Sprint 12+). Null for legacy offers and for
   *  offers created before the wizard rehaul (Sprint 13). */
  preset_id?: string | null;
  is_lead_magnet?: boolean;
  shows_as_lead_magnet?: boolean;
  // Wizard-driven: will this offer run in editions/cohorts/batches?
  has_editions?: boolean;

  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  status: OfferStatus;

  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;

  pricing?: PricingStructure[];
  currency?: string;

  // Polymorphic details
  specific_details?: Record<string, unknown>;

  // Stats & Metadata
  active_clients?: number; // From specific_details or computed
  metadata_info?: Record<string, unknown>;

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
  prerequisites?: unknown[]; // Flexible schema — shape depends on offer type
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
    [key: string]: unknown;
  };

  // Lifecycle (SaaS archive + soft-delete)
  archived_at?: string | null;
}

export interface DeliverableItem {
  name: string;
  format: string; // Should match DeliverableFormat enum values
  quantity: string;
  value_stack_price: number;
}

// Re-exported from lib/api/avatar — canonical definition lives there to avoid lib→feature dependency
export type { AvatarDefinition } from "@/lib/api/avatar";

export interface ObjectionItem {
  id?: string;
  type: string; // "price" | "time" | "trust" | "partner" | "custom"
  trigger_phrases: string[];
  strategy: string;
  rebuttal: string;
}

/** @deprecated Use ObjectionItem instead */
export type Objection = ObjectionItem;

/** Temporal pricing tier — Phase 4. Half-open window `[valid_from, valid_until)`. */
export interface PricingTier {
  label: string;
  pricing: PricingStructure[];
  /** ISO 8601 UTC string, or null for open-ended start. */
  valid_from: string | null;
  /** ISO 8601 UTC string, or null for open-ended end. */
  valid_until: string | null;
  sort_order: number;
}

export interface LaunchEdition {
  id: string;
  offer_id: string;
  edition_name: string;
  edition_number: number;
  /**
   * Sprint 7 6th SSoT axis — what kind of variant this row represents.
   * Always present post Sprint 15.1 (every archetype supports variants).
   */
  variant_structure: VariantStructure;
  /**
   * Sprint 7 — structure-specific payload. Keys vary by ``variant_structure``:
   * TIER → ``features[]`` + ``price_amount`` + ``price_currency``.
   * SKU_VARIANT → ``attributes{}`` + ``sku_code``.
   * REGIONAL → ``country_codes[]`` + ``currency``.
   * MODALITY → ``mode``.
   * LANGUAGE → ``locale``.
   * Temporal structures usually leave it empty.
   */
  structure_data: Record<string, unknown>;
  sort_rank: number | null;
  /** Nullable for DRAFT placeholder editions that have not been filled yet. */
  start_date: string | null;
  end_date: string | null;
  registration_start: string | null;
  registration_end: string | null;
  timezone: string;
  /** @deprecated Use `pricing_tiers` instead. Kept for read-path compat only. */
  pricing_override: PricingStructure[] | null;
  pricing_tiers: PricingTier[];
  /** Tier whose window contains "now" (computed server-side). */
  active_tier: PricingTier | null;
  effective_pricing: PricingStructure[];
  currency: string;
  capacity: number | null;
  enrollment_count: number;
  status: EditionStatus;
  visibility: EditionVisibility;
  /** True when this edition is the auto-created placeholder (no date, no pricing override, DRAFT + PRIVATE). */
  is_placeholder: boolean;
  location_override: Record<string, unknown> | null;
  notes: string | null;
  /** Set when this edition was created by cloning another (Phase 3 provenance). */
  cloned_from_edition_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LaunchEditionCreate {
  edition_name?: string;
  /** Optional: placeholder editions may be created without a date. */
  start_date?: string;
  end_date?: string;
  registration_start?: string;
  registration_end?: string;
  timezone?: string;
  pricing_override?: PricingStructure[];
  pricing_tiers?: PricingTier[];
  capacity?: number;
  location_override?: Record<string, unknown>;
  notes?: string;
}

export interface LaunchEditionUpdate {
  edition_name?: string;
  start_date?: string;
  end_date?: string;
  registration_start?: string;
  registration_end?: string;
  timezone?: string;
  pricing_override?: PricingStructure[] | null;
  pricing_tiers?: PricingTier[] | null;
  capacity?: number;
  enrollment_count?: number;
  status?: EditionStatus;
  visibility?: EditionVisibility;
  location_override?: Record<string, unknown>;
  notes?: string;
}

/** Strategy picker for cloning an edition's landing. Phase 3. */
export type EditionCloneStrategy = "literal" | "date_replace" | "ai_regen";

export interface EditionClonePayload {
  strategy: EditionCloneStrategy;
  new_edition_input: LaunchEditionCreate;
  changes_brief?: string;
  attachment_ids?: string[];
}

export interface EditionCloneResponse {
  edition: LaunchEdition;
  landing_id: string | null;
  landing_slug: string | null;
  asset_ids: string[];
}

/** Edition-scoped landing lookup response. */
export interface EditionLandingResponse {
  landing_id: string | null;
  slug: string | null;
  is_published: boolean;
}
