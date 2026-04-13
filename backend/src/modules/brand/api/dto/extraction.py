"""Brand extraction DTOs."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractRequest(BaseModel):
    """Request schema for extract."""

    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field(
        "brand_identity",
        description="Type of extraction to perform",
    )


class BrandVisualsResponse(BaseModel):
    """Response DTO for brand visuals extraction (extract_data endpoint)."""

    # Core colors
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    background_color: str | None = None
    surface_color: str | None = None
    text_primary_color: str | None = None
    text_secondary_color: str | None = None
    text_on_primary: str | None = None
    text_on_secondary: str | None = None

    # Extended colors
    color_palette: list[str] = Field(default_factory=list)
    neutral_colors: list[str] = Field(default_factory=list)
    semantic_colors: dict[str, str | None] | None = None
    gradient_definitions: list[str] = Field(default_factory=list)
    color_usage_rules: str | None = None

    # Typography
    font_heading: str | None = None
    font_body: str | None = None
    font_accent: str | None = None
    font_weights: dict[str, Any] | None = None
    typography_scale: dict[str, str] | None = None

    # Design system
    border_radius_style: str | None = None
    border_radius_values: dict[str, str] | None = None
    shadow_style: str | None = None
    spacing_base: str | None = None
    visual_density: str | None = None

    # Visual personality
    brand_mood: dict[str, Any] | None = None
    visual_references: str | None = None
    photography_style: str | None = None
    icon_style: str | None = None

    # Style
    style_preset: str | None = None
    design_style: str | None = None
    usage_guidelines: list[str] = Field(default_factory=list)

    # Assets
    logo_url: str | None = None
    favicon_url: str | None = None
    images: list[str] = Field(default_factory=list)
    logos: dict[str, str | None] | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ExtractFullBrandResponse(BaseModel):
    """Response DTO for full brand extraction job dispatch (202 Accepted)."""

    job_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ExtractionStatusResponse(BaseModel):
    """Response DTO for polling extraction job status."""

    status: str
    progress: int | None = None
    stage: str | None = None
    started_at: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ExtractionTraceResponse(BaseModel):
    """Response DTO for a single brand extraction trace."""

    id: str
    job_id: str
    mode: str
    profile_name: str
    url: str | None = None
    include_visuals: str | None = None
    include_assets: str | None = None
    status: str
    sections_total: int | None = None
    sections_succeeded: int | None = None
    total_duration_s: float | None = None
    content_length: int | None = None
    error_message: str | None = None
    events: list[Any] = Field(default_factory=list)
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExtractionTraceSummaryResponse(BaseModel):
    """Response DTO for trace list items (no events field)."""

    id: str
    job_id: str
    mode: str
    profile_name: str
    url: str | None = None
    status: str
    sections_total: int | None = None
    sections_succeeded: int | None = None
    total_duration_s: float | None = None
    content_length: int | None = None
    error_message: str | None = None
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
