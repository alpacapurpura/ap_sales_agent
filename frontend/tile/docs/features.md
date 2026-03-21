# Feature Modules

Feature modules in `src/features/` follow Feature-Sliced Design (FSD). Each feature encapsulates components, hooks, API calls, and TypeScript types for a specific business domain.

---

## Brand Feature (`src/features/brand/`)

Manages brand identity, strategy, visuals, testimonials, team, and authority proof.

### Entry Point

```typescript
import { brandApi } from "@/features/brand/api";
import type {
  BrandSettings,
  BrandIdentity,
  BrandStrategy,
  BrandStory,
  BrandVisuals,
  BrandLogos,
  ContactData,
  TestimonialItem,
  AuthorityItem,
  KeyFigure,
  FullBrandExtractionRequest,
  BrandTeam,
  BrandMethodologyPillar,
  BrandCompetitor,
  BrandStoryMilestone,
} from "@/features/brand/types";
```

### Types

```typescript { .api }
interface BrandIdentity {
  brand_name?: string;
  industry?: string;
  website?: string;
  logo_url?: string;
  tagline?: string;
  description?: string;
  founding_year?: string;
  timezone?: string;
  language?: string;
  // Legal fields
  legal_name?: string;
  tax_id?: string;
  fiscal_address?: string;
  legal_representative?: string;
  terms_url?: string;
  privacy_url?: string;
  // Visual fields (legacy - prefer BrandVisuals)
  primary_color?: string;
  accent_color?: string;
  font_heading?: string;
  font_body?: string;
  background_color?: string;
  text_primary_color?: string;
  text_on_primary?: string;
  design_style?: string;
  usage_guidelines?: string[];
}

interface BrandMethodologyPillar {
  id: string;
  title: string;
  description?: string;
}

interface BrandCompetitor {
  id: string;
  name: string;
  differentiation?: string;
}

interface BrandStrategy {
  value_proposition?: string;
  target_audience?: string;
  differentiation?: string;
  offerings?: string[];
  unique_value_proposition?: string;
  competitors: BrandCompetitor[];
  methodology_name?: string;
  methodology_description?: string;
  methodology_pillars: BrandMethodologyPillar[];
}

interface BrandStoryMilestone {
  id: string;
  year: string;
  title: string;
  description?: string;
}

interface BrandStory {
  origin_story?: string;
  mission?: string;
  vision?: string;
  milestones?: BrandStoryMilestone[];
}

interface BrandTeam {
  /** @deprecated Prefer KeyFigure[] in BrandSettings.team */
  key_leadership: string[];
  team_structure: string;
  culture_vibe: string;
  locations: string[];
}

interface KeyFigure {
  id: string;
  name: string;
  role: string;
  headshot_url?: string;
  is_primary_voice?: boolean;
  bio?: string;
  gender?: string;
  communication_style?: string;
  personal_website?: string;
  personal_linkedin?: string;
  personal_instagram?: string;
  personal_tiktok?: string;
  personal_facebook?: string;
  work_whatsapp?: string;
  gallery?: string[];  // Array of image URLs
}

interface BrandLogos {
  primary?: string;     // URL
  secondary?: string;   // URL
  icon?: string;        // URL
  dark_mode?: string;   // URL — logo variant for dark mode
  light_mode?: string;  // URL — logo variant for light mode
  main?: string;        // URL (legacy alias)
  inverted?: string;    // URL (legacy alias)
  favicon?: string;     // URL (legacy alias)
}

interface SemanticColors {
  success?: string;
  error?: string;
  warning?: string;
  info?: string;
}

interface BrandMood {
  adjectives?: string[];
  energy?: "low" | "medium" | "high";
}

interface BrandVisuals {
  // Colors (core)
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
  surface_color?: string;
  text_primary_color?: string;
  text_secondary_color?: string;
  text_on_primary?: string;
  text_on_secondary?: string;
  // Colors (extended)
  color_palette?: string[];
  neutral_colors?: string[];
  semantic_colors?: SemanticColors;
  gradient_definitions?: string[];
  color_usage_rules?: string;
  // Typography
  font_heading?: string;
  font_body?: string;
  font_accent?: string;
  font_weights?: Record<string, number[]>;
  typography_scale?: Record<string, string>;
  // Design System
  border_radius_style?: string;
  border_radius_values?: Record<string, string>;
  shadow_style?: string;
  spacing_base?: string;
  visual_density?: string;
  // Visual Personality
  brand_mood?: BrandMood;
  visual_references?: string;
  photography_style?: string;
  icon_style?: string;
  style_preset?: string;
  design_style?: string;
  usage_guidelines?: string[];
  // Assets
  logo_url?: string;
  favicon_url?: string;
  images?: string[];
  logos?: BrandLogos;
}

interface ContactData {
  support_email?: string;
  sales_email?: string;
  phone?: string;
  whatsapp?: string;
  address?: string;
  website?: string;
  social_instagram?: string;
  social_linkedin?: string;
  social_youtube?: string;
  social_tiktok?: string;
  social_facebook?: string;
  social_twitter?: string;
  testimonials_url?: string;
}

interface TestimonialItem {
  id: string;
  type: "text" | "video";
  content: string;
  author_name: string;
  author_role: string;
  rating: number;
  author_avatar?: string;
}

interface AuthorityItem {
  id: string;
  entity_name: string;
  type: string;     // e.g. "press", "award", "certification"
  context: string;
  proof_url: string;
  logo_url?: string;
}

interface BrandSettings {
  identity?: BrandIdentity;
  strategy?: BrandStrategy;
  story?: BrandStory;
  team?: KeyFigure[];             // current usage
  visuals?: BrandVisuals;
  contact?: ContactData;
  testimonials?: TestimonialItem[];
  authority_vault?: AuthorityItem[];
  team_metadata?: BrandTeam;     // legacy
}

interface FullBrandExtractionRequest {
  url?: string;
  text?: string;
  mode: "initial" | "update";
  update_instructions?: string;
}
```

### Brand API

```typescript { .api }
const brandApi: {
  /** Fetch complete brand settings. Returns {} for new tenants (404). */
  getBrandSettings(token: string): Promise<BrandSettings>;
  /** Update brand settings (PATCH — partial update supported) */
  updateBrandSettings(data: BrandSettings, token: string): Promise<BrandSettings>;
  /** Extract brand visuals from a URL using AI */
  extractBrandVisuals(url: string, token: string): Promise<BrandVisuals>;
  /** Full AI-powered brand extraction from URL/text or FormData */
  extractFullBrand(data: FullBrandExtractionRequest | FormData, token: string): Promise<BrandSettings>;
};
```

### Offer Form Schema

The `OfferFormValues` type is the form/API input shape used by `createOffer` and `saveOffer`. It mirrors `Offer` but uses snake_case for pricing and includes additional validation fields:

```typescript { .api }
interface OfferFormValues {
  id?: string;
  internal_sku?: string | null;
  public_name: string;          // required
  type: OfferType;              // required
  offer_value_level?: OfferValueLevel | null;
  delivery_model?: OfferDeliveryModel | null;
  headline_promise?: string;
  avatar_id?: string | null;
  target_avatar_match?: AvatarPersona[];
  marketing_pain_points?: string[];
  marketing_desires?: string[];
  objections?: ObjectionItem[];
  primary_outcome?: string;
  time_to_value?: string;
  access_duration?: AccessDuration | null;
  access_duration_text?: string | null;
  support_duration_days?: number | null;
  instructors?: string[];
  requires_application?: boolean;
  min_financial_capacity?: FinancialCapacity;
  prerequisites?: (PrerequisiteType | string)[];
  anti_avatar_keywords?: string[];
  pricing_options?: PricingStructure[];   // Note: key differs from Offer.pricing
  price_pay_in_full?: number | null;
  currency?: string;
  guarantee_type?: GuaranteeType;
  guarantee_terms?: string | null;
  downsell_offer_id?: string | null;
  upsell_offer_id?: string | null;
  includes_offers?: string[];
  deliverables?: DeliverableItem[];
  assets?: OfferAsset[];
  onboarding_action?: OnboardingMechanism | null;
  onboarding_url?: string | null;
  vsl_link?: string | null;
  checkout_page_url?: string | null;
  calendar_type_id?: string | null;
  status?: OfferStatus;
  specific_details?: Record<string, any> | null;
}
```

### Offer API

```typescript { .api }
import { offerApi } from "@/features/offer-studio/api";

const offerApi: {
  /** List all offers for the current tenant */
  listOffers(token: string): Promise<Offer[]>;

  /** Get a single offer by ID */
  getOffer(id: string, token: string): Promise<Offer>;

  /** Create a new offer */
  createOffer(data: OfferFormValues, token: string): Promise<Offer>;

  /** Partially update an offer (PATCH) */
  saveOffer(id: string, data: Partial<OfferFormValues>, token: string): Promise<any>;

  /**
   * Update a specific section of an offer via a dedicated endpoint.
   * @param sectionId - One of: "identity" | "strategy" | "promise" | "psychology" |
   *   "pricing" | "closing" | "instructors" | "value_stack" | "resources" | "gallery" |
   *   "program_details" | "product_details" | "service_details" | "event_details" | "subscription_details"
   *   Falls back to saveOffer for unknown sectionId values.
   */
  saveSection(id: string, sectionId: string, data: any, token: string): Promise<any>;

  /** Generate psychological framing (pain points & desires) for an offer */
  generatePsychology(data: OfferPsychologyPayload, token: string): Promise<{ pains: string[]; desires: string[] }>;

  /** Fetch the landing page config for an offer. Returns null if not yet generated (404). */
  getLandingConfig(offerId: string, token: string): Promise<any | null>;

  /** Generate an AI landing page for the offer (POST /api/v1/landings/) */
  generateLandingPage(offerId: string, token: string): Promise<any>;

  /** Update landing page config (PATCH /api/v1/landings/offer/{offerId}) */
  updateLandingPage(offerId: string, config: any, token: string): Promise<any>;

  /**
   * Regenerate a single landing page block with AI instructions.
   * @param blockType - The block type identifier
   * @param currentContent - Current block content
   * @param instruction - Natural language instruction for AI
   */
  regenerateBlock(offerId: string, blockType: string, currentContent: any, instruction: string, token: string): Promise<any>;
};
```

---

## Audit Feature (`src/features/audit/`)

Monitors AI agent conversations, trace executions, and LLM logs for debugging and quality assurance.

### Entry Point

```typescript
import {
  AuditDashboard,
  useAuditLeads,
  useLeadDetails,
  useLeadTimeline,
  useTraceDetails,
  clearLeadHistory,
} from "@/features/audit";
import type { AuditLead, TimelineEvent, TraceDetail, LLMLog, LeadDetails } from "@/features/audit";
```

### Types

```typescript { .api }
interface AuditLead {
  lead: {
    id: string;
    full_name: string;
    telegram_id: string | null;
    whatsapp_id: string | null;
    created_at: string; // ISO datetime
  };
  last_activity: string; // ISO datetime
}

interface TimelineEvent {
  type: "message" | "trace";
  id: string;
  timestamp: number;
  created_at: string;
  // Message fields
  role?: string;        // "user" | "assistant"
  content?: string;
  // Trace fields
  node_name?: string;
  execution_time_ms?: number;
  llm_summary?: {
    model: string;
    total_tokens: number;
    prompt_template?: string;
  } | null;
}

interface TraceDetail {
  id: string;
  node_name: string;
  input_state: any;
  output_state: any;
  execution_time_ms: number;
  created_at: string;
  llm_logs: LLMLog[];
}

interface LLMLog {
  id: string;
  model: string;
  prompt_template: string;
  prompt_rendered: string;
  response_text: string;
  tokens_input: number;
  tokens_output: number;
  metadata: any;
}

interface LeadDetails {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  telegram_id: string | null;
  whatsapp_id: string | null;
  instagram_id: string | null;
  tiktok_id: string | null;
  profile_data: any;
  created_at: string;
  updated_at: string;
}
```

### Hooks (TanStack Query)

```typescript { .api }
/** Returns all leads with audit data */
function useAuditLeads(): UseQueryResult<AuditLead[]>;

/** Returns detailed info for a specific lead (enabled only when leadId is non-null) */
function useLeadDetails(leadId: string | null): UseQueryResult<LeadDetails>;

/** Returns interleaved messages and traces for a lead (enabled only when leadId is non-null) */
function useLeadTimeline(leadId: string | null): UseQueryResult<TimelineEvent[]>;

/** Returns execution details for a specific trace (enabled only when traceId is non-null) */
function useTraceDetails(traceId: string | null): UseQueryResult<TraceDetail>;
```

### API Functions

```typescript { .api }
/** Deletes all conversation history for a lead */
async function clearLeadHistory(token: string, leadId: string): Promise<any>;
```

### Components

```typescript { .api }
/** Full audit dashboard UI with lead list, timeline, and trace inspector */
function AuditDashboard(): JSX.Element;
```

---

## Settings Feature (`src/features/settings/`)

User/tenant settings management components and hooks.

### Entry Point

```typescript
import {
  WebhookView,
  AIKeysForm,
  GeneralSettingsForm,
  ProfileView,
} from "@/features/settings";
import { useUserProfile, useTenants } from "@/features/settings/hooks/use-profile";
```

### Hooks

```typescript { .api }
import { useUserProfile } from "@/features/settings/hooks/use-profile";
import { useTenants } from "@/features/settings/hooks/use-tenants";

/** Returns current user profile (SystemUserProfile). Cached 5 minutes. Re-fetches on tenant switch. */
function useUserProfile(): UseQueryResult<SystemUserProfile>;

/** Returns list of tenants for current user. Cached 5 minutes. */
function useTenants(): UseQueryResult<Tenant[]>;
```

### Components

```typescript { .api }
/** Webhook settings view with URL display and secret regeneration */
function WebhookView(): JSX.Element;

/** Form to configure OpenAI and Gemini API keys */
function AIKeysForm(): JSX.Element;

/** Form to update general tenant settings (default currency, etc.) */
function GeneralSettingsForm(): JSX.Element;

/** User profile view displaying name, email, and tenant info */
function ProfileView(): JSX.Element;
```

---

## Connections Feature (`src/features/connections/`)

UI components for managing third-party service integrations.

### Entry Point

```typescript
import { GoogleWorkspaceView, TelegramView } from "@/features/connections";
```

### Components

```typescript { .api }
/** Google Workspace OAuth connection management (Calendar, Gmail, Analytics) */
function GoogleWorkspaceView(): JSX.Element;

/** Telegram bot connection management */
function TelegramView(): JSX.Element;
```

---

## Marketing Studio Feature (`src/features/marketing-studio/`)

Customer lifecycle analytics and growth metrics types.

### Entry Point

```typescript
import type {
  LifecycleStage,
  RFMData,
  CustomerProfile,
  JourneyEvent,
} from "@/features/marketing-studio/types";
```

### Types

```typescript { .api }
type LifecycleStage = "lead" | "onboarding" | "active" | "at_risk" | "churned";

interface RFMData {
  recency: number;       // days since last purchase
  frequency: number;     // number of purchases
  monetary: number;      // total spend
  rfm_score: number;
  segment: string;       // e.g. "Champions", "At Risk"
}

interface CustomerProfile {
  id: string;
  full_name: string;
  email?: string;
  lifecycle_stage: LifecycleStage;
  ltv: number;           // lifetime value
  rfm?: RFMData;
  tags: string[];
}

interface JourneyEvent {
  id: string;
  type: "email" | "click" | "purchase" | "visit" | "message" | string;
  occurred_at: string;   // ISO datetime
  metadata?: Record<string, any>;
}
```

---

## Offer Studio Feature (`src/features/offer-studio/`)

Offer management, landing page editor, and offer ladder builder.

### Entry Point

```typescript
import type {
  Offer, OfferType, OfferStatus, OfferValueLevel, OfferDeliveryModel,
  AvatarDefinition, PricingStructure, DeliverableItem, ObjectionItem,
  OfferAsset, AssetType, GuaranteeType, OnboardingMechanism,
  DeliverableFormat, FinancialCapacity, MarketingAsset,
  FulfillmentType, DigitalFormat, ProgramStructure, LiveInteractionType,
  CommunityPlatform, ServiceCategory, InteractionMode, ServiceFrequency,
  EventLocationType, AccommodationType, PaymentPlanType, AccessDuration,
  PrerequisiteType, BillingFrequency, AvatarPersona,
} from "@/features/offer-studio/types";
import type { OfferFormValues } from "@/features/offer-studio/types/schema";
import { offerApi } from "@/features/offer-studio/api";
```

### Enums

```typescript { .api }
enum OfferValueLevel { N0 = "N0", N1 = "N1", N2 = "N2", N3 = "N3", N4 = "N4", N5 = "N5", N6 = "N6" }

enum OfferDeliveryModel { DIY = "DIY", DWY = "DWY", DFY = "DFY", B2B = "B2B" }

enum OfferType {
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

enum OfferStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  PAUSED = "PAUSED",
  ARCHIVED = "ARCHIVED",
  WAITLIST = "WAITLIST",
  SOLD_OUT = "SOLD_OUT",
}

enum GuaranteeType {
  UNCONDITIONAL_X_DAY = "UNCONDITIONAL_X_DAY",
  CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED",
  EXCHANGE_ONLY = "EXCHANGE_ONLY",
  NO_REFUNDS = "NO_REFUNDS",
}

enum DeliverableFormat {
  LIVE_GROUP_CALL = "LIVE_GROUP_CALL",
  ONE_ON_ONE_CALL = "1ON1_CALL",
  RECORDED_CONTENT = "RECORDED_CONTENT",
  PHYSICAL_SHIPMENT = "PHYSICAL_SHIPMENT",
  DFY_ASSET = "DFY_ASSET",
}

enum FinancialCapacity { LOW = "LOW", MEDIUM = "MEDIUM", HIGH = "HIGH", ULTRA_HIGH = "ULTRA_HIGH" }

enum OnboardingMechanism {
  CHECKOUT_LINK = "SEND_LINK",
  CALENDAR_BOOKING = "BOOK_CALL",
  INTAKE_FORM = "INTAKE_FORM",
  COMMUNITY_INVITE = "JOIN_COMMUNITY",
}

enum AssetType {
  IMAGE = "IMAGE",
  VIDEO = "VIDEO",
  AUDIO = "AUDIO",
  PDF = "PDF",
  TXT = "TXT",
  URL = "URL",
}

enum FulfillmentType {
  DIRECT_DOWNLOAD = "DIRECT_DOWNLOAD",
  EXTERNAL_PLATFORM_ACCESS = "EXTERNAL_PLATFORM",
  PHYSICAL_SHIPPING = "PHYSICAL_SHIPPING",
}

enum DigitalFormat {
  PDF_DOCUMENT = "PDF",
  VIDEO_FILE = "MP4/MOV",
  AUDIO_FILE = "MP3",
  SPREADSHEET = "XLS/CSV",
  NOTION_TEMPLATE = "NOTION",
  ZIP_BUNDLE = "ZIP",
  SAAS_ACCESS = "SAAS_KEY",
  PHYSICAL_ITEM = "PHYSICAL",
}

enum ProgramStructure {
  FIXED_DATE_COHORT = "FIXED_COHORT",
  ROLLING_ADMISSION = "ROLLING_EVERGREEN",
  CHALLENGE_SPRINT = "CHALLENGE",
}

enum LiveInteractionType {
  GROUP_Q_AND_A = "GROUP_Q&A",
  WORKSHOP_PRACTICAL = "WORKSHOP",
  LIVE_PROGRAM_DELIVERY = "LIVE_PROGRAM_DELIVERY",
  HYBRID_SUPPORT = "HYBRID",
  NO_LIVE_COMPONENTS = "ASYNC_ONLY",
}

enum CommunityPlatform {
  WHATSAPP_TELEGRAM = "CHAT_APP",
  FACEBOOK_GROUP = "FB_GROUP",
  CIRCLE_SKOOL = "DEDICATED_PLATFORM",
  DISCORD_SLACK = "CHAT_SERVER",
  ZOOM = "ZOOM",
  GOOGLE_MEETS = "GOOGLE_MEETS",
  NONE = "NONE",
}

enum ServiceCategory {
  ADVISORY_CONSULTING = "ADVISORY",
  DONE_FOR_YOU_AGENCY = "EXECUTION_AGENCY",
  B2B_AUTHORITY_RENTAL = "AUTHORITY_RENTAL",
}

enum InteractionMode {
  SYNCHRONOUS_LIVE = "SYNC_LIVE",
  ASYNC_DELIVERY = "ASYNC_DELIVERY",
  HYBRID_MODEL = "HYBRID",
}

enum ServiceFrequency {
  ONE_OFF_PROJECT = "ONE_OFF",
  RETAINER_RECURRING = "RETAINER",
  PACK_OF_SESSIONS = "PACK",
}

enum EventLocationType {
  VIRTUAL_REMOTE = "VIRTUAL",
  IN_PERSON_LOCAL = "IN_PERSON_LOCAL",
  DESTINATION_RETREAT = "DESTINATION_RETREAT",
}

enum AccommodationType {
  NOT_INCLUDED = "NOT_INCLUDED",
  SHARED_ROOM = "SHARED_ROOM",
  PRIVATE_ROOM = "PRIVATE_ROOM",
  LUXURY_SUITE = "LUXURY_SUITE",
}

enum PaymentPlanType {
  PAY_IN_FULL = "PAY_IN_FULL",
  INTERNAL_SPLIT_PAY = "SPLIT_PAY",
  THIRD_PARTY_FINANCE = "3RD_PARTY",
  SUBSCRIPTION_RECURRING = "SUBSCRIPTION",
}

enum AccessDuration {
  LIFETIME_CONTENT = "LIFETIME",
  LIMITED_TIME_ACCESS = "LIMITED_TIME",
  DURATION_OF_PAYMENT = "PAY_TO_PLAY",
  HYBRID_ACCESS = "HYBRID_ACCESS",
}

enum PrerequisiteType {
  NO_PREREQUISITE = "NONE",
  GENDER_IDENTITY = "GENDER_IDENTITY",
  REVENUE_LEVEL = "REVENUE_LEVEL",
  BUSINESS_STAGE = "BUSINESS_STAGE",
}

enum BillingFrequency {
  MONTHLY = "MONTHLY",
  QUARTERLY = "QUARTERLY",
  YEARLY = "YEARLY",
}

enum AvatarPersona {
  BEGINNER = "BEGINNER",
  INTERMEDIATE = "INTERMEDIATE",
  ADVANCED = "ADVANCED",
  EXPERT = "EXPERT",
}
```

### Interfaces

```typescript { .api }
interface PricingStructure {
  label: string;
  plan_type?: string;
  total_amount: number;
  currency?: string;
  deposit_required?: number;
  number_of_installments?: number;
  installment_amount?: number;
}

interface DeliverableItem {
  name: string;
  format: string; // DeliverableFormat value
  quantity: string;
  value_stack_price: number;
}

interface ObjectionItem {
  id?: string;
  type: string;            // "price" | "time" | "trust" | "partner" | "custom"
  trigger_phrases: string[];
  strategy: string;
  rebuttal: string;
}

interface OfferAsset {
  id?: string;
  type: AssetType;
  name: string;
  url: string;
  size?: string;
  trigger_context?: string;
  is_knowledge_base?: boolean;
}

interface AvatarDefinition {
  icp_description?: string;    // Ideal Customer Profile description
  anti_avatar?: string;        // Who is NOT a fit
  voice_tone_config?: Record<string, any>;
  pain_points?: string[];
  desires?: string[];
  awareness_level?: string;
  sophistication_level?: string;
}

interface MarketingAsset {
  id: string;
  name: string;
  type: string;
  size?: string;
  url?: string;
}

interface Offer {
  id: string;
  name: string;
  public_name?: string;
  internal_sku?: string;
  type: OfferType;
  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  status: OfferStatus;
  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;
  pricing?: PricingStructure[];
  currency?: string;
  specific_details?: Record<string, any>;
  active_clients?: number;
  metadata_info?: Record<string, any>;
  avatar_id?: string;
  marketing_pain_points?: string[];
  marketing_desires?: string[];
  objections?: ObjectionItem[];
  deliverables?: DeliverableItem[];
  assets?: OfferAsset[];
  target_avatar_match?: string[];
  prerequisites?: any[];
  includes_offers?: string[];
  guarantee_type?: GuaranteeType;
  guarantee_terms?: string;
  access_duration?: string;
  access_duration_text?: string;  // Human-readable duration e.g. "1 Year"
  support_duration_days?: number;
  instructors?: string[];         // Array of instructor IDs or names
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

/** @deprecated Use ObjectionItem instead */
type Objection = ObjectionItem;
```

---

## Sales Feature (`src/features/sales/`)

AI sales dashboard, pipeline, and lead management components.

### Entry Point

```typescript
import type { Lead, LeadTemperature, LeadStatus, LeadCustomer } from "@/features/sales/types";
```

### Types

```typescript { .api }
type LeadTemperature = "cold" | "warm" | "hot";
type LeadStatus = "new" | "contacted" | "qualified" | "proposal" | "won" | "lost";

interface LeadCustomer {
  id: string;
  full_name?: string;
  email?: string;
  phone?: string;
  avatar_url?: string;
  social_handle?: string;
}

interface Lead {
  id: string;
  name?: string;
  avatarUrl?: string;
  initials?: string;
  role?: string;
  company?: string;
  email?: string;
  phone?: string;
  score: number;
  temperature: LeadTemperature;
  status: LeadStatus;
  lastActivity?: string;
  nextAction?: string;
  tags?: string[];
  customer?: LeadCustomer;
  ai_memory?: string;
}
```

---

## App Router

The application uses Next.js App Router with the following key route structures:

### Multi-Tenant Dashboard (`src/app/(main)/[tenantId]/`)

```
/[tenantId]/                    → Dashboard home
/(dashboard)/brand-settings/    → Brand Studio
/(dashboard)/marketing-studio/  → Growth/marketing analytics
/(dashboard)/offer-studio/      → Offer management
/(dashboard)/offer-studio/offer/[id]/  → Offer editor
/(dashboard)/sales/             → Sales pipeline dashboard
/(dashboard)/settings/          → Settings
/(dashboard)/avatars/           → Avatar management
/(dashboard)/avatars/[id]/edit/ → Avatar editor
/(dashboard)/audit/             → AI audit log
/(dashboard)/admin/tenants/     → Admin tenant management (superadmin only)
```

### Public Routes

```
/book/[tenant_slug]/[event_slug]         → Public event booking page
/(public)/p/[slug]                       → Public landing page
/[tenantId]/preview/[offerId]            → Offer preview
/[tenantId]/editor/[offerId]             → Landing page visual editor (Puck)
/visit/[token]                           → Token-based visit redirect
/onboarding/                             → New tenant onboarding
```

### OAuth Callback Routes

```
/connections/meta/callback          → Meta OAuth callback
/connections/google/callback        → Google OAuth callback
/api/auth/shopify/callback          → Shopify OAuth callback
```

### Authentication

Authentication is provided by Clerk. All protected routes require sign-in. The application redirects to `/sign-in` on 401 and `/forbidden` on 403. Tenant context is derived from the `[tenantId]` URL segment and injected as `X-Tenant-ID` header by `fetchClient`.

---

## Shared Layout Components (`src/components/shared/layout/`)

### SidebarProvider & useSidebar

Persistent collapsible sidebar state management using localStorage.

```typescript { .api }
import { SidebarProvider, useSidebar } from "@/components/shared/layout/sidebar-context";

interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
}

/** Context provider for sidebar state — wrap app layout */
function SidebarProvider(props: { children: React.ReactNode }): JSX.Element;

/** Hook to access sidebar state and controls — must be inside SidebarProvider */
function useSidebar(): SidebarContextType;
```

### AppSidebar

Main application navigation sidebar. Renders as a collapsible desktop sidebar and a Sheet-based mobile sidebar. Reads tenant context from the URL path.

```typescript { .api }
import { AppSidebar } from "@/components/shared/layout/app-sidebar";

/** Renders desktop sidebar (fixed, collapsible) and mobile hamburger + sheet nav */
function AppSidebar(): JSX.Element;
```

Place inside `SidebarProvider` in the root layout. Automatically uses `useSidebar()`, `useUserProfile()`, and `useTenants()` internally.

### TenantSwitcher

Dropdown for switching the active tenant. On selection, updates localStorage (`x-tenant-id`) and performs a hard redirect to `/{tenantId}/brand-settings`.

```typescript { .api }
import { TenantSwitcher } from "@/components/shared/layout/tenant-switcher";
import type { TenantProfile } from "@/lib/api/settings";

interface TenantSwitcherProps {
  currentTenant: TenantProfile | null;
  isCollapsed: boolean;         // renders icon-only button when true
  activeTenantId?: string;      // highlights the active tenant in the list
}

function TenantSwitcher(props: TenantSwitcherProps): JSX.Element;
```

### ModeToggle

Button that toggles between light and dark themes via `next-themes`. Renders a sun/moon icon pair.

```typescript { .api }
import { ModeToggle } from "@/components/shared/mode-toggle";

/** Ghost icon button to toggle light/dark theme. SSR-safe (hydration guard). */
function ModeToggle(): JSX.Element;
```

---

## Providers (`src/components/providers/`)

### ThemeProvider

Wraps the application with theme support (next-themes). Place at app root.

```typescript { .api }
import { ThemeProvider } from "@/components/providers/theme-provider";
// Props: all next-themes ThemeProviderProps
// Common props: attribute, defaultTheme, enableSystem, disableTransitionOnChange
```

---

## Auth Components (`src/components/auth/`)

### TenantGuard

Server Component that enforces tenant context. Renders `ForbiddenPage` if the authenticated user has no tenant. Allows `/onboarding` route to bypass the check.

```typescript { .api }
import { TenantGuard } from "@/components/auth/tenant-guard";

/** Server Component — renders children if user has tenant, ForbiddenPage otherwise */
async function TenantGuard(props: { children: ReactNode }): Promise<JSX.Element>;
```

Requires middleware to set `x-current-path` header for path-based bypass logic.

---

## Error Components (`src/components/shared/`)

### ErrorBoundary

React class component that catches unhandled errors in its subtree and renders a full-screen fallback UI with a "Reload Page" button.

```typescript { .api }
import ErrorBoundary from "@/components/shared/error-boundary";

/** Class component error boundary. Wrap sections that may throw runtime errors. */
class ErrorBoundary extends React.Component<{ children?: ReactNode }> {}
```

**Usage:**
```typescript
<ErrorBoundary>
  <SomeFeatureComponent />
</ErrorBoundary>
```
