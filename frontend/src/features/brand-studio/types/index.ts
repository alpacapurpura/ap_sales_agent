export interface BrandIdentity {
  // Core Identity
  brand_name?: string;
  industry?: string;
  // business_types moved to tenant-profile on 2026-04-20 — see
  // features/tenant-profile/types/tenant-profile.ts

  // Extended Identity (Matching Form & Validation)
  website?: string;
  logo_url?: string;
  tagline?: string;
  description?: string;
  founding_year?: string;
  timezone?: string;
  language?: string;
  voice_tone?: string;

  // Legal — fiscal core
  legal_name?: string;
  legal_entity_type?: string;
  tax_id?: string;
  tax_regime?: string;
  country_of_registration?: string;
  commercial_registry_number?: string;
  fiscal_address?: string;
  legal_representative?: string;

  // Legal — contact
  legal_email?: string;
  dpo_email?: string;

  // Legal — URLs
  terms_url?: string;
  privacy_url?: string;
  cookies_url?: string;
  refund_policy_url?: string;
  acceptable_use_url?: string;

  // Legal — regulated profession (optional)
  regulated_profession_body?: string;
  professional_license_number?: string;
  professional_license_holder?: string;
  operating_authorization?: string;
  liability_insurance_carrier?: string;

  // Legal — sales-agent guardrails (internal)
  sales_agent_disclaimer?: string;
  sales_agent_out_of_scope?: string;
  escalation_contact?: string;
}

export interface BrandMethodologyPillar {
  id: string;
  title: string;
  description?: string;
}

export interface BrandCompetitor {
  id: string;
  name: string;
  differentiation?: string;
}

export interface BrandStrategy {
  methodology_name?: string;
  methodology_description?: string;
  methodology_pillars: BrandMethodologyPillar[];
}

export interface BrandStoryMilestone {
  id: string;
  year: string;
  title: string;
  description?: string;
}

export interface BrandStory {
  origin_story?: string;
  mission?: string;
  vision?: string;
  milestones?: BrandStoryMilestone[];
}

export interface KeyFigure {
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
  gallery?: string[];
}

export interface BrandLogos {
  primary?: string;
  secondary?: string; // Icon
  dark_mode?: string;
  light_mode?: string;
  // Legacy support
  main?: string;
  inverted?: string;
  favicon?: string;
}

export interface SemanticColors {
  success?: string;
  error?: string;
  warning?: string;
  info?: string;
}

export interface BrandMood {
  adjectives?: string[];
  energy?: "low" | "medium" | "high";
}

export interface BrandVisuals {
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

  // Style
  style_preset?: string;
  design_style?: string;
  usage_guidelines?: string[];

  // Assets
  logo_url?: string;
  favicon_url?: string;
  images?: string[];
  logos?: BrandLogos;
}

export interface ContactData {
  support_email?: string;
  sales_email?: string;
  phone?: string;
  whatsapp?: string;
  address?: string;
  social_instagram?: string;
  social_linkedin?: string;
  social_youtube?: string;
  social_tiktok?: string;
  social_facebook?: string;
  social_twitter?: string;
  testimonials_url?: string;
}

/**
 * @deprecated Removed from the frontend as part of the social_proof SSoT
 * migration. Use the ``Testimonial`` type from ``@/lib/api/testimonial``.
 * The alias below keeps legacy snapshots compiling; new code must not
 * reference ``TestimonialSnapshot``.
 */
export interface TestimonialSnapshot {
  id: string;
  type: "text" | "video";
  content: string;
  author_name: string;
  author_role: string;
  rating: number;
  author_avatar?: string;
}

export interface AuthorityItem {
  id: string;
  entity_name: string;
  type: string;
  context: string;
  proof_url: string;
  logo_url?: string;
}

// --- Brand Love Key (Positioning) ---

export interface CompetitiveEnvironment {
  technical_enemy?: string;
  philosophical_enemy?: string;
  direct_competitors: BrandCompetitor[];
  indirect_competitors: BrandCompetitor[];
}

export interface ConsumerInsight {
  tension?: string;
  observation?: string;
  implication?: string;
}

export interface BrandBenefits {
  functional_benefits: string[];
  emotional_benefits: string[];
}

/**
 * Personality data shared by Sales Agent + Brand Studio. Fields moved out
 * of the old ``BrandPositioning.values`` block in Sprint 2.D so the
 * Personality section owns them end-to-end (see backend ``BrandPersonality``
 * VO).
 */
export interface BrandPersonality {
  core_values?: string[];
  personality_traits?: string[];
  /** Jungian archetype — one of the 12-option enum used in the schema. */
  archetype?: string;
}

export interface ReasonToBelieve {
  id: string;
  type?: string;
  statement?: string;
  proof_url?: string;
}

export interface BrandPositioning {
  unique_value_proposition?: string;
  competitive_environment?: CompetitiveEnvironment;
  insight?: ConsumerInsight;
  benefits?: BrandBenefits;
  reasons_to_believe: ReasonToBelieve[];
  discriminator?: string;
  brand_essence?: string;
}

// --- StoryBrand (Narrative) ---

export interface StoryBrandHero {
  identity?: string;
  desire?: string;
}

export interface StoryBrandProblem {
  villain?: string;
  external_problem?: string;
  internal_problem?: string;
  philosophical_problem?: string;
}

export interface StoryBrandGuide {
  empathy_statement?: string;
  authority_statement?: string;
}

export interface StoryBrandPlanStep {
  id: string;
  step_number: number;
  title?: string;
  description?: string;
}

export interface StoryBrandCTA {
  direct_cta?: string;
  transitional_cta?: string;
}

export interface StoryBrandOutcome {
  success_transformation?: string;
  failure_consequence?: string;
}

export interface BrandNarrative {
  hero?: StoryBrandHero;
  problem?: StoryBrandProblem;
  guide?: StoryBrandGuide;
  plan: StoryBrandPlanStep[];
  cta?: StoryBrandCTA;
  outcome?: StoryBrandOutcome;
  one_liner?: string;
}

// --- Communication Assets ---

export interface CreativeConcept {
  id: string;
  name?: string;
  description?: string;
  tone?: string;
}

export interface FunnelAsset {
  id: string;
  funnel_stage?: string;
  asset_type?: string;
  title?: string;
  idea?: string;
  copy_draft?: string;
  objective?: string;
  concept_id?: string;
  status?: string;
}

export interface CommunicationAssets {
  creative_concepts: CreativeConcept[];
  assets: FunnelAsset[];
  custom_asset_types: string[];
}

// --- BrandSettings ---

export interface BrandSettings {
  identity?: BrandIdentity;
  strategy?: BrandStrategy;
  story?: BrandStory;

  // Updated to reflect current usage in TeamManager
  team?: KeyFigure[];

  // Extended fields
  visuals?: BrandVisuals;
  contact?: ContactData;
  // Legacy JSONB arrays — read-only from this layer. The SSoT for these
  // three collections is now the social_proof module (see
  // /api/v1/social-proof/). New code MUST use the social_proof API.
  testimonials?: TestimonialSnapshot[];
  authority_vault?: AuthorityItem[];

  // Strategic frameworks
  positioning?: BrandPositioning;
  narrative?: BrandNarrative;
  communication_assets?: CommunicationAssets;

  // Personality (Sales Agent + Brand Studio) — absorbs the old
  // positioning.values block from Sprint 2.D.
  brand_personality?: BrandPersonality;
}

// Helper types for API requests if needed
export interface FullBrandExtractionRequest {
  url?: string;
  text?: string;
  mode: "initial" | "update";
  update_instructions?: string;
}

// ExtractedVisuals removed — use BrandVisuals directly
