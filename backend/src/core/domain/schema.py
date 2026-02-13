from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, Literal, List
from enum import Enum
from .lead_enums import FinancialCapacity, SophisticationLevel, AuthorityLevel, LeadTemperature, AvatarPersona, PipelineStage

class FunnelStage(str, Enum):
    RAPPORT = "S1_Rapport"
    DISCOVERY = "S2_Discovery"
    GAP = "S3_Gap"
    PITCH = "S4_Pitch"
    ANCHORING = "S5_Anchoring"
    CLOSING = "S6_Closing"
    DOWNSELL_EXIT = "DOWNSELL_EXIT"

class LeadStatus(str, Enum):
    AWARENESS = "awareness"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEGOTIATION = "negotiation"
    ENROLLED = "enrolled"
    OBJECTION_HANDLING = "objection_handling"
    CALL_BOOKED = "call_booked"
    DOWNSELL_ACCEPTED = "downsell_accepted"

class ProductLaunchStage(str, Enum):
    PRE_LAUNCH = "pre_launch"
    OPEN_CART = "open_cart"
    CLOSE_CART = "close_cart"
    EVERGREEN = "evergreen"

class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"

class PromptSource(str, Enum):
    HYBRID = "hybrid"   # DB > File (Default)
    FILE = "file"       # Local File System only (Dev)
    DB = "db"           # DB Only (Strict Prod)

class BusinessStage(str, Enum):
    ACTIVE = "Negocio Activo"
    IDEA = "Idea Clara"
    NONE = "Sin Idea"

# class FinancialTier(str, Enum): -> Replaced by FinancialCapacity
# class DecisionMaker(str, Enum): -> Replaced by AuthorityLevel

class UserProfile(BaseModel):
    """
    The 'Valeria' Profile.
    Centralizes all user data extracted during conversation.
    """
    model_config = ConfigDict(extra='ignore')

    # --- Identidad (Optional) ---
    name: Optional[str] = Field(None, description="Client's first name (The Lead)")
    age: Optional[str] = Field(None, description="Client's age")
    email: Optional[str] = Field(None, description="Client's email")
    phone: Optional[str] = Field(None, description="Client's phone number")
    gender: Optional[Literal["Masculino", "Femenino", "No binario"]] = Field(None, description="Client's gender")
    
    occupation: Optional[str] = Field(None, description="Job title or role (e.g. Therapist, Lawyer)")
    location: Optional[str] = Field(None, description="City or Country")
    timezone: Optional[str] = Field(None, description="Timezone (e.g. GMT-5)")
    social_handle: Optional[str] = Field(None, description="Instagram/LinkedIn handle")
    
    # --- Contexto de la Consulta (Terceros) ---
    user: Optional[Literal["himself", "Other"]] = Field("himself", description="Is the user inquiring for themselves or others?")
    relation: Optional[Literal["friend", "partner", "wife", "coworker", "daughter"]] = Field(None, description="Relation to the real client if user='Other'")
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
    missing_fields: list[str] = Field(default_factory=list, description="Fields that are mandatory/desirable but null")

class IncomingMessage(BaseModel):
    """
    Modelo unificado para mensajes entrantes de cualquier canal.
    Normaliza la entrada antes de que llegue al Agente.
    """
    user_id: str = Field(..., description="Identificador único del usuario en el canal origen")
    text: str = Field(..., description="Contenido textual del mensaje")
    channel_type: Literal["telegram", "whatsapp", "manychat", "web"] = Field(..., description="Canal de origen")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Datos extra del canal (nombre, teléfono, etc.)")

class OutgoingMessage(BaseModel):
    """
    Modelo unificado para respuestas del Agente.
    Los adaptadores convertirán esto al formato específico del canal.
    """
    user_id: str
    text: str
    message_type: Literal["text", "template", "image"] = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AISettings(BaseModel):
    """
    Configuration for AI API Keys (Tenant level).
    """
    openai_api_key: Optional[str] = Field(None, description="User provided OpenAI API Key")
    gemini_api_key: Optional[str] = Field(None, description="User provided Gemini API Key")
    can_use_platform_keys: bool = Field(False, description="Whether the tenant is allowed to use platform keys")

class TenantSettingsUpdate(BaseModel):
    """
    Request model for updating Tenant AI settings.
    """
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class TenantPermissionUpdate(BaseModel):
    """
    Request model for Superadmin to update permissions.
    """
    can_use_platform_keys: bool

class WebhookSettings(BaseModel):
    """
    Configuration for External Webhook Access.
    """
    webhook_url: str
    webhook_secret: Optional[str] = Field(None, description="The secret key to authenticate requests")

class GeneralSettings(BaseModel):
    """
    General Tenant Configuration (e.g. currency, timezone).
    """
    default_currency: str = Field("USD", description="Default currency code (ISO 4217)")
    timezone: str = Field("UTC", description="Default timezone (e.g. America/Lima)")

class TenantProfile(BaseModel):
    id: str
    name: str
    slug: str
    timezone: str = "UTC"

class SystemUserProfile(BaseModel):
    """
    Response model for current authenticated user profile.
    """
    id: str
    full_name: Optional[str]
    email: str
    tenant: Optional[TenantProfile]

class GeneralSettingsUpdate(BaseModel):
    """
    Request model for updating General Settings.
    """
    default_currency: str
    timezone: str

class BrandIdentity(BaseModel):
    """
    Extracted visual identity of a brand.
    Expanded to capture a basic Design System.
    """
    # --- Core Colors ---
    primary_color: str = Field(..., description="Main brand color (hex code e.g., #FF0000). Look for 'background-color' or 'color' styles on primary buttons, headers, or logos.")
    accent_color: str = Field(..., description="Secondary/Accent color (hex code). Look for call-to-action buttons, highlights, or links.")
    
    # --- Extended Palette ---
    background_color: str = Field("#FFFFFF", description="Main page background color (usually white or very light gray). Found in body or main container.")
    text_primary_color: str = Field("#000000", description="Main text color (usually black or very dark gray). Found in body or p tags.")
    text_on_primary: str = Field("#FFFFFF", description="Text color to use on top of primary color elements (accessibility). Check button text colors.")
    
    # --- Typography ---
    font_heading: Optional[str] = Field(None, description="Font family used for headings (h1, h2).")
    font_body: Optional[str] = Field(None, description="Font family used for body text.")
    
    # --- Context & Rules ---
    design_style: str = Field(..., description="Brief style description (e.g., 'Minimalist, Clean, Corporate', 'Vibrant, Playful', 'Luxury, Dark Mode'). Infer from colors and font choices.")
    usage_guidelines: List[str] = Field(default_factory=list, description="Inferred rules for using the visual assets (e.g., 'Use primary color for buttons', 'Headers are dark', 'Cards have shadows').")
