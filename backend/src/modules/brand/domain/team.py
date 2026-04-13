"""Brand team value objects."""

from typing import Any

from pydantic import ConfigDict, Field, model_validator

from src.shared.domain.base_entity import BaseEntity


class KeyFigure(BaseEntity):
    """Represent key figure data."""

    id: str
    name: str
    role: str
    headshot_url: str | None = None
    is_primary_voice: bool | None = None
    bio: str | None = None
    gender: str | None = None
    communication_style: str | None = None
    personal_website: str | None = None
    personal_linkedin: str | None = None
    personal_instagram: str | None = None
    personal_tiktok: str | None = None
    personal_facebook: str | None = None
    work_whatsapp: str | None = None
    gallery: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class BrandTeamWrapper(BaseEntity):
    """Represent brand team wrapper data."""

    key_leadership: list[KeyFigure] = Field(
        default_factory=list,
        description="Personas clave identificadas",
    )
    culture_vibe: str | None = Field(None, description="Descripción de la cultura")
    locations: str | None = Field(None, description="Ubicaciones operativas")


class BrandContact(BaseEntity):
    """Represent brand contact data."""

    # Frontend ContactData fields
    support_email: str | None = None
    sales_email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    address: str | None = None
    social_instagram: str | None = None
    social_linkedin: str | None = None
    social_youtube: str | None = None
    social_tiktok: str | None = None
    social_facebook: str | None = None
    social_twitter: str | None = None
    testimonials_url: str | None = None

    # Legacy fields fallback
    email: str | None = None
    social: dict[str, Any] | None = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:  # noqa: ANN401
        """Migrate legacy fields (email, website, social dict) into structured fields."""
        if isinstance(data, dict):
            # 1. Migrate email -> support_email
            if not data.get("support_email") and data.get("email"):
                data["support_email"] = data["email"]

            # 2. Migrate social dict -> flat fields
            social_data = data.get("social")
            if isinstance(social_data, dict):
                mapping = {
                    "instagram": "social_instagram",
                    "linkedin": "social_linkedin",
                    "youtube": "social_youtube",
                    "tiktok": "social_tiktok",
                    "facebook": "social_facebook",
                    "twitter": "social_twitter",
                }
                for key, target_field in mapping.items():
                    if not data.get(target_field) and social_data.get(key):
                        data[target_field] = social_data[key]

        return data


class BrandTestimonial(BaseEntity):
    """Represent brand testimonial data."""

    # Frontend TestimonialItem fields
    id: str | None = None
    type: str | None = "text"  # "text" | "video"
    content: str | None = None
    author_name: str | None = None
    author_role: str | None = None
    rating: int | None = 5
    author_avatar: str | None = None

    # Legacy fields
    author: str | None = None
    role: str | None = None
    quote: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_testimonial(cls, data: Any) -> Any:  # noqa: ANN401
        """Execute migrate legacy testimonial operation."""
        if isinstance(data, dict):
            if not data.get("author_name") and data.get("author"):
                data["author_name"] = data["author"]
            if not data.get("author_role") and data.get("role"):
                data["author_role"] = data["role"]
            if not data.get("content") and data.get("quote"):
                data["content"] = data["quote"]
            if not data.get("author_avatar") and data.get("avatar_url"):
                data["author_avatar"] = data["avatar_url"]
        return data


class BrandAuthorityItem(BaseEntity):
    """Represent brand authority item data."""

    # Frontend AuthorityItem fields
    id: str | None = None
    entity_name: str | None = None
    type: str | None = None
    context: str | None = None
    proof_url: str | None = None
    logo_url: str | None = None

    # Legacy fields
    title: str | None = None
    url: str | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_authority(cls, data: Any) -> Any:  # noqa: ANN401
        """Execute migrate legacy authority operation."""
        if isinstance(data, dict):
            if not data.get("entity_name") and data.get("title"):
                data["entity_name"] = data["title"]
            if not data.get("proof_url") and data.get("url"):
                data["proof_url"] = data["url"]
        return data


class BrandTeam(BaseEntity):
    """Hold legacy information about the people behind the brand.

    Kept for backward compatibility or metadata.
    """

    key_leadership: list[str] = Field(default_factory=list)
    team_structure: str | None = Field(None)
    culture_vibe: str | None = Field(None)
    locations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
