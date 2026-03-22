// Frontend Types Mirroring Backend Enums & Schemas

export enum LandingPageArchetype {
  THE_SQUEEZE = "THE_SQUEEZE",
  THE_EVENT = "THE_EVENT",
  THE_FLASH_OFFER = "THE_FLASH_OFFER",
  THE_TRANSFORMER = "THE_TRANSFORMER",
  THE_VELVET_ROPE = "THE_VELVET_ROPE",
  THE_BROCHURE = "THE_BROCHURE",
}

export enum LandingPageThemeColor {
  DEFAULT = "DEFAULT",
  OCEAN = "OCEAN",
  SUNSET = "SUNSET",
  FOREST = "FOREST",
  LUXURY = "LUXURY",
  MINIMAL = "MINIMAL",
}

export enum LandingPageFont {
  SANS_SERIF = "SANS_SERIF",
  SERIF = "SERIF",
  MODERN = "MODERN",
}

export interface FeatureBullet {
  icon?: string;
  title: string;
  description?: string;
}

export interface Testimonial {
  author_name: string;
  author_role?: string;
  content: string;
  avatar_url?: string;
}

export interface LandingPageTheme {
  primary_color: string;
  secondary_color: string;
  font_pair: LandingPageFont;
  dark_mode: boolean;
}

// --- CONTENT TYPES ---

export interface SqueezeContent {
  headline: string;
  subheadline: string;
  visual_url?: string;
  bullets: string[];
  cta_text: string;
  privacy_text?: string;
}

export interface EventContent {
  headline: string;
  event_date: string; // ISO String
  hook_question: string;
  secret_bullets: string[];
  speaker_name: string;
  speaker_bio: string;
  speaker_image_url?: string;
  cta_text: string;
}

export interface FlashOfferContent {
  headline: string;
  offer_name: string;
  problem_agitation: string;
  solution_description: string;
  original_price: number;
  discounted_price: number;
  guarantee_text: string;
  cta_text: string;
  product_image_url?: string;
}

export interface TransformerContent {
  headline: string;
  subheadline: string;
  problem_text: string;
  agitation_text: string;
  solution_text: string;
  method_name: string;
  method_description: string;
  authority_name: string;
  authority_bio: string;
  authority_image_url?: string;
  modules: FeatureBullet[];
  bonuses: FeatureBullet[];
  price_anchor: string;
  price_offer: string;
  scarcity_text: string;
  cta_text: string;
  testimonials: Testimonial[];
  story_hook?: string;
  hero_layout?: "centered" | "split" | "background" | "vsl" | "urgency" | "quiz";
  video_url?: string;
}

export interface VelvetRopeContent {
  headline: string;
  manifesto_text: string;
  who_is_this_for: string[];
  who_is_NOT_for: string[];
  experience_image_urls: string[];
  scarcity_text: string;
  cta_text: string;
}

export interface BrochureContent {
  headline: string;
  authority_logos: string[];
  process_steps: FeatureBullet[];
  deliverables: string[];
  case_studies: Testimonial[];
  cta_text: string;
}

// --- MASTER CONFIG ---

export type LandingPageContent = 
  | SqueezeContent 
  | EventContent 
  | FlashOfferContent 
  | TransformerContent 
  | VelvetRopeContent 
  | BrochureContent
  | Record<string, any>; // Puck Data Support

export interface LandingPageConfig {
  archetype: LandingPageArchetype;
  theme: LandingPageTheme;
  content: LandingPageContent;
  slug: string;
  seo_title?: string;
  seo_description?: string;
  is_published: boolean;
}
