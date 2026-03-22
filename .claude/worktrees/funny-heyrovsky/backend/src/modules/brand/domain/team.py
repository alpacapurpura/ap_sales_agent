from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict, model_validator
from src.shared.domain.base_entity import BaseEntity

class KeyFigure(BaseEntity):
    id: str
    name: str
    role: str
    headshot_url: Optional[str] = None
    is_primary_voice: Optional[bool] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    communication_style: Optional[str] = None
    personal_website: Optional[str] = None
    personal_linkedin: Optional[str] = None
    personal_instagram: Optional[str] = None
    personal_tiktok: Optional[str] = None
    personal_facebook: Optional[str] = None
    work_whatsapp: Optional[str] = None
    gallery: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra='allow')

class BrandTeamWrapper(BaseEntity):
    key_leadership: List[KeyFigure] = Field(default_factory=list, description="Personas clave identificadas")
    culture_vibe: Optional[str] = Field(None, description="Descripción de la cultura")
    locations: Optional[str] = Field(None, description="Ubicaciones operativas")

class BrandContact(BaseEntity):
    # Frontend ContactData fields
    support_email: Optional[str] = None
    sales_email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    address: Optional[str] = None
    social_instagram: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_youtube: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_facebook: Optional[str] = None
    social_twitter: Optional[str] = None
    testimonials_url: Optional[str] = None
    
    # Legacy fields fallback
    email: Optional[str] = None
    website: Optional[str] = None
    social: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        """
        Migrate legacy fields (email, website, social dict) into structured fields.
        """
        if isinstance(data, dict):
            # 1. Migrate email -> support_email
            if not data.get('support_email') and data.get('email'):
                data['support_email'] = data['email']
            
            # 2. Migrate social dict -> flat fields
            social_data = data.get('social')
            if isinstance(social_data, dict):
                mapping = {
                    'instagram': 'social_instagram',
                    'linkedin': 'social_linkedin',
                    'youtube': 'social_youtube',
                    'tiktok': 'social_tiktok',
                    'facebook': 'social_facebook',
                    'twitter': 'social_twitter'
                }
                for key, target_field in mapping.items():
                    if not data.get(target_field) and social_data.get(key):
                        data[target_field] = social_data[key]
            
            # 3. Migrate website -> specialized fields if applicable?
            # For now, keep website as fallback if needed, but no direct mapping to testimonials_url
            
        return data

class BrandTestimonial(BaseEntity):
    # Frontend TestimonialItem fields
    id: Optional[str] = None
    type: Optional[str] = "text" # "text" | "video"
    content: Optional[str] = None
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    rating: Optional[int] = 5
    author_avatar: Optional[str] = None
    
    # Legacy fields
    author: Optional[str] = None
    role: Optional[str] = None
    quote: Optional[str] = None
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_testimonial(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get('author_name') and data.get('author'):
                data['author_name'] = data['author']
            if not data.get('author_role') and data.get('role'):
                data['author_role'] = data['role']
            if not data.get('content') and data.get('quote'):
                data['content'] = data['quote']
            if not data.get('author_avatar') and data.get('avatar_url'):
                data['author_avatar'] = data['avatar_url']
        return data

class BrandAuthorityItem(BaseEntity):
    # Frontend AuthorityItem fields
    id: Optional[str] = None
    entity_name: Optional[str] = None
    type: Optional[str] = None
    context: Optional[str] = None
    proof_url: Optional[str] = None
    logo_url: Optional[str] = None
    
    # Legacy fields
    title: Optional[str] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_authority(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get('entity_name') and data.get('title'):
                data['entity_name'] = data['title']
            if not data.get('proof_url') and data.get('url'):
                data['proof_url'] = data['url']
        return data

class BrandTeam(BaseEntity):
    """
    Legacy Information about the people behind the brand.
    Kept for backward compatibility or metadata.
    """
    key_leadership: List[str] = Field(default_factory=list)
    team_structure: Optional[str] = Field(None)
    culture_vibe: Optional[str] = Field(None)
    locations: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra='allow')
