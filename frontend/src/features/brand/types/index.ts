export interface BrandIdentity {
    // Core Identity
    brand_name?: string;
    industry?: string;
    
    // NOTE: Visual fields (colors, fonts, styles) have been moved to BrandVisuals
    // to align with Backend Domain Models. Use BrandVisuals for all aesthetic properties.
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

export interface BrandStory {
    origin_story?: string;
    mission?: string;
    vision?: string;
    milestones?: string[];
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

export interface BrandVisuals {
    // Colors
    primary_color?: string;
    accent_color?: string;
    background_color?: string;
    text_primary_color?: string;
    text_on_primary?: string;

    // Typography
    font_heading?: string;
    font_body?: string;

    // Style
    style_preset?: string;
    design_style?: string;
    usage_guidelines?: string[];

    // Assets
    logo_url?: string;
    images?: string[]; // Made optional to be safe
    logos?: {
        primary?: string;
        secondary?: string; // Icon
        dark_mode?: string;
        light_mode?: string;
        // Legacy support
        main?: string;
        inverted?: string;
        favicon?: string;
    };
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

// Re-export specific types if they are used as standalone in components
export type ExtractedVisuals = BrandIdentity; // Alias for backward compatibility if needed
