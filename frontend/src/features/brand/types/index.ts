export interface BrandIdentity {
    brand_name?: string;
    legal_name?: string;
    tax_id?: string;
    fiscal_address?: string;
    website?: string;
    industry?: string;
    logo_url?: string;
    timezone?: string;
    language?: string;
    
    // Identity
    tagline?: string;
    description?: string;
    founding_year?: string;

    // Legal
    legal_representative?: string;
    terms_url?: string;
    privacy_url?: string;
}

export interface BrandStoryMilestone {
    id: string;
    year: string;
    title: string;
    description?: string;
}

export interface BrandStory {
    origin_story?: string;
    milestones: BrandStoryMilestone[];
}

export interface BrandCompetitor {
    id: string;
    name: string;
    differentiation?: string;
}

export interface BrandLogos {
    primary?: string;
    secondary?: string;
    dark_mode?: string;
    light_mode?: string;
}

export interface BrandMethodologyPillar {
    id: string;
    title: string;
    description?: string;
}

export interface BrandStrategy {
    unique_value_proposition?: string;
    competitors: BrandCompetitor[];
    methodology_name?: string;
    methodology_description?: string;
    methodology_pillars: BrandMethodologyPillar[];
}

export interface KeyFigure {
    id: string;
    name: string;
    role?: string;
    is_primary_voice: boolean;
    bio?: string;
    gender?: "Masculino" | "Femenino" | "Neutro";
    communication_style?: string;
    headshot_url?: string;
    gallery?: string[];
    personal_website?: string;
    personal_linkedin?: string;
    personal_instagram?: string;
    personal_tiktok?: string;
    personal_facebook?: string;
    work_whatsapp?: string;
}

export interface AuthorityItem {
    id: string;
    entity_name: string;
    type?: string;
    context?: string;
    proof_url?: string;
    logo_url?: string;
}

export interface TestimonialItem {
    id: string;
    type: "text" | "video";
    content: string;
    author_name: string;
    author_role?: string;
    author_avatar?: string;
    rating?: number;
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

export interface BrandVisuals {
    primary_color: string;
    accent_color: string;
    font_heading: string;
    font_body: string;
    style_preset?: string;
    
    // Brand Assets
    logos?: BrandLogos;

    // Extended Palette
    background_color?: string;
    text_primary_color?: string;
    text_on_primary?: string;
    
    // Context
    design_style?: string;
    usage_guidelines?: string[];
}

export interface BrandSettings {
    identity: BrandIdentity;
    story: BrandStory;
    strategy: BrandStrategy;
    visuals: BrandVisuals;
    team: KeyFigure[];
    testimonials: TestimonialItem[];
    authority_vault: AuthorityItem[];
    contact: ContactData;
}

export interface ExtractedVisuals {
    primary_color: string;
    accent_color: string;
    font_heading?: string;
    font_body?: string;
    
    // Extended Palette
    background_color: string;
    text_primary_color: string;
    text_on_primary: string;
    
    // Context
    design_style: string;
    usage_guidelines: string[];
}

export interface FullBrandExtractionRequest {
    url?: string;
    text?: string;
    mode: "initial" | "update";
    update_instructions?: string;
}
