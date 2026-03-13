from typing import Optional, List, Dict, Any
from pydantic import Field
from datetime import datetime
from uuid import UUID
from src.shared.domain.base_entity import BaseEntity
from src.modules.crm.domain.enums import (
    FinancialCapacity, SophisticationLevel, AuthorityLevel, 
    LeadTemperature, AvatarPersona, BusinessStage
)

class UserProfile(BaseEntity):
    """
    The 'Valeria' Profile.
    Centralizes all user data extracted during conversation.
    """
    # --- Identidad (Optional) ---
    name: Optional[str] = Field(None, description="Client's first name (The Lead)")
    age: Optional[str] = Field(None, description="Client's age")
    email: Optional[str] = Field(None, description="Client's email")
    phone: Optional[str] = Field(None, description="Client's phone number")
    gender: Optional[str] = Field(None, description="Client's gender")
    
    occupation: Optional[str] = Field(None, description="Job title or role (e.g. Therapist, Lawyer)")
    location: Optional[str] = Field(None, description="City or Country")
    timezone: Optional[str] = Field(None, description="Timezone (e.g. GMT-5)")
    social_handle: Optional[str] = Field(None, description="Instagram/LinkedIn handle")
    
    # --- Contexto de la Consulta (Terceros) ---
    user: Optional[str] = Field("himself", description="Is the user inquiring for themselves or others?")
    relation: Optional[str] = Field(None, description="Relation to the real client if user='Other'")
    user_name: Optional[str] = Field(None, description="Name of the person inquiring (if user='Other')")

    # --- Calificación (Mandatory) ---
    business_stage: Optional[BusinessStage] = Field(None, description="Current stage of their business journey")
    financial_tier: Optional[FinancialCapacity] = Field(None, description="Estimated financial capacity (BROKE_STUDENT, etc.)")
    sophistication: Optional[SophisticationLevel] = Field(None, description="Awareness level (UNAWARE, PROBLEM_AWARE, etc.)")
    authority: Optional[AuthorityLevel] = Field(None, description="Decision making authority (SOLO, PARTNER, etc.)")
    temperature: Optional[LeadTemperature] = Field(None, description="Lead temperature (COLD, WARM, HOT)")
    
    # --- Datos del Negocio (New) ---
    business_name: Optional[str] = Field(None, description="Name of the user's business")
    business_industry: Optional[str] = Field(None, description="Industry or niche of the business")
    business_details: Optional[str] = Field(None, description="Relevant history, founding story, or key details about the business")

    # --- Psicografía (Desirable) ---
    main_pain_point: Optional[str] = Field(None, description="Primary struggle (e.g. Burnout, Chaos)")
    main_goal: Optional[str] = Field(None, description="Primary desire (e.g. Freedom, Scale)")
    assigned_persona: Optional[AvatarPersona] = Field(None, description="The archetype to use (NEWBIE, SKEPTIC, VIP)")
    
    # --- Metadata de Progreso ---
    missing_fields: List[str] = Field(default_factory=list, description="Fields that are mandatory/desirable but null")

class Lead(BaseEntity):
    """
    Lead Domain Model (Pydantic).
    Represents a potential customer interacting via various channels.
    """
    id: UUID
    tenant_id: Optional[UUID] = None
    
    # Customer Link
    customer_id: Optional[UUID] = None
    
    # Channel specific IDs
    telegram_id: Optional[str] = None
    whatsapp_id: Optional[str] = None
    instagram_id: Optional[str] = None
    tiktok_id: Optional[str] = None
    api_id: Optional[str] = None
    
    # Profile Data
    profile_data: UserProfile = Field(default_factory=UserProfile)
    
    # Dynamic Scoring & System Flags
    fit_score: Optional[int] = 0
    intent_score: Optional[int] = 0
    temperature: Optional[str] = "COLD"
    is_blacklisted: Optional[bool] = False

    last_interaction_date: Optional[datetime] = None
    next_scheduled_action: Optional[datetime] = None

    # Deep Memory
    conversation_summary: Optional[str] = None
    key_objections_history: Optional[List[Any]] = Field(default_factory=list)

    # Style / Persona Data
    style_profile: Optional[Dict[str, Any]] = None
    custom_system_instruction: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
