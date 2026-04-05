from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.crm.domain.enums import (
    AuthorityLevel,
    AvatarPersona,
    BusinessStage,
    FinancialCapacity,
    LeadTemperature,
    SophisticationLevel,
)
from src.shared.domain.base_entity import BaseEntity


class UserProfile(BaseEntity):
    """
    The 'Valeria' Profile.
    Centralizes all user data extracted during conversation.
    """

    # --- Identidad (Optional) ---
    name: str | None = Field(None, description="Client's first name (The Lead)")
    age: str | None = Field(None, description="Client's age")
    email: str | None = Field(None, description="Client's email")
    phone: str | None = Field(None, description="Client's phone number")
    gender: str | None = Field(None, description="Client's gender")

    occupation: str | None = Field(
        None, description="Job title or role (e.g. Therapist, Lawyer)"
    )
    location: str | None = Field(None, description="City or Country")
    timezone: str | None = Field(None, description="Timezone (e.g. GMT-5)")
    social_handle: str | None = Field(None, description="Instagram/LinkedIn handle")

    # --- Contexto de la Consulta (Terceros) ---
    user: str | None = Field(
        "himself", description="Is the user inquiring for themselves or others?"
    )
    relation: str | None = Field(
        None, description="Relation to the real client if user='Other'"
    )
    user_name: str | None = Field(
        None, description="Name of the person inquiring (if user='Other')"
    )

    # --- Calificación (Mandatory) ---
    business_stage: BusinessStage | None = Field(
        None, description="Current stage of their business journey"
    )
    financial_tier: FinancialCapacity | None = Field(
        None, description="Estimated financial capacity (BROKE_STUDENT, etc.)"
    )
    sophistication: SophisticationLevel | None = Field(
        None, description="Awareness level (UNAWARE, PROBLEM_AWARE, etc.)"
    )
    authority: AuthorityLevel | None = Field(
        None, description="Decision making authority (SOLO, PARTNER, etc.)"
    )
    temperature: LeadTemperature | None = Field(
        None, description="Lead temperature (COLD, WARM, HOT)"
    )

    # --- Datos del Negocio (New) ---
    business_name: str | None = Field(None, description="Name of the user's business")
    business_industry: str | None = Field(
        None, description="Industry or niche of the business"
    )
    business_details: str | None = Field(
        None,
        description="Relevant history, founding story, or key details about the business",
    )

    # --- Psicografía (Desirable) ---
    main_pain_point: str | None = Field(
        None, description="Primary struggle (e.g. Burnout, Chaos)"
    )
    main_goal: str | None = Field(
        None, description="Primary desire (e.g. Freedom, Scale)"
    )
    assigned_persona: AvatarPersona | None = Field(
        None, description="The archetype to use (NEWBIE, SKEPTIC, VIP)"
    )

    # --- Metadata de Progreso ---
    missing_fields: list[str] = Field(
        default_factory=list, description="Fields that are mandatory/desirable but null"
    )


class Lead(BaseEntity):
    """
    Lead Domain Model (Pydantic).
    Represents a potential customer interacting via various channels.
    """

    id: UUID
    tenant_id: UUID | None = None

    # Customer Link
    customer_id: UUID | None = None

    # Channel specific IDs
    telegram_id: str | None = None
    whatsapp_id: str | None = None
    instagram_id: str | None = None
    tiktok_id: str | None = None
    api_id: str | None = None

    # Profile Data
    profile_data: UserProfile = Field(default_factory=UserProfile)

    # Dynamic Scoring & System Flags
    fit_score: int | None = 0
    intent_score: int | None = 0
    temperature: str | None = "COLD"
    is_blacklisted: bool | None = False

    last_interaction_date: datetime | None = None
    next_scheduled_action: datetime | None = None

    # Deep Memory
    conversation_summary: str | None = None
    key_objections_history: list[Any] | None = Field(default_factory=list)

    # Style / Persona Data
    style_profile: dict[str, Any] | None = None
    custom_system_instruction: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
