export interface BrandIdentity {
    // Core Identity
    brand_name?: string;
    industry?: string;

    // Extended Identity (Matching Form & Validation)
    website?: string;
    logo_url?: string;
    tagline?: string;
    description?: string;
    founding_year?: string;
    timezone?: string;
    language?: string;

    // Legal Fields
    legal_name?: string;
    tax_id?: string;
    fiscal_address?: string;
    legal_representative?: string;
    terms_url?: string;
    privacy_url?: string;

    // NOTE: Visual fields (colors, fonts, styles) have been moved to BrandVisuals
    // to align with Backend Domain Models. Use BrandVisuals for all aesthetic properties.
    // These are kept here for legacy/backward compatibility with wizard extraction flow.
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
    value_proposition?: string;
    target_audience?: string;
    differentiation?: string;
    offerings?: string[];

    // Active fields (DB Sync)
    unique_value_proposition?: string;
    competitors: BrandCompetitor[];
    
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

export interface BrandTeam {
    // Legacy structure kept for backward compatibility if needed, 
    // but preferred usage is via KeyFigure[] in BrandSettings.team
    key_leadership: string[];
    team_structure: string;
    culture_vibe: string;
    locations: string[];
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
    website?: string;
    social_instagram?: string;
    social_linkedin?: string;
    social_youtube?: string;
    social_tiktok?: string;
    social_facebook?: string;
    social_twitter?: string;
    testimonials_url?: string;
}

export interface TestimonialItem {
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

export interface BrandSettings {
    identity?: BrandIdentity;
    strategy?: BrandStrategy;
    story?: BrandStory;
    
    // Updated to reflect current usage in TeamManager
    team?: KeyFigure[]; 
    
    // Extended fields
    visuals?: BrandVisuals;
    contact?: ContactData;
    testimonials?: TestimonialItem[];
    authority_vault?: AuthorityItem[];
    
    // Legacy field support (optional)
    team_metadata?: BrandTeam;
}

// Helper types for API requests if needed
export interface FullBrandExtractionRequest {
    url?: string;
    text?: string;
    mode: "initial" | "update";
    update_instructions?: string;
}

// ExtractedVisuals removed — use BrandVisuals directly
