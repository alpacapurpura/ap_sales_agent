from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, Literal
from enum import Enum

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

class FinancialTier(str, Enum):
    HIGH = "High (Comfortable)"
    MEDIUM = "Medium (Stretch but possible)"
    LOW = "Low (Survival)"

class DecisionMaker(str, Enum):
    SOLO = "Sola"
    PARTNER = "Con Socio/Esposo"

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
    
    # --- Contexto de la Consulta (Terceros) ---
    user: Optional[Literal["himself", "Other"]] = Field("himself", description="Is the user inquiring for themselves or others?")
    relation: Optional[Literal["friend", "partner", "wife", "coworker", "daughter"]] = Field(None, description="Relation to the real client if user='Other'")
    user_name: Optional[str] = Field(None, description="Name of the person inquiring (if user='Other')")

    # --- Calificación (Mandatory) ---
    business_stage: Optional[BusinessStage] = Field(None, description="Current stage of their business journey")
    financial_tier: Optional[FinancialTier] = Field(None, description="Estimated financial capacity")
    
    # --- Datos del Negocio (New) ---
    business_name: Optional[str] = Field(None, description="Name of the user's business")
    business_industry: Optional[str] = Field(None, description="Industry or niche of the business")
    business_details: Optional[str] = Field(None, description="Relevant history, founding story, or key details about the business")

    # --- Psicografía (Desirable) ---
    main_pain_point: Optional[str] = Field(None, description="Primary struggle (e.g. Burnout, Chaos)")
    main_goal: Optional[str] = Field(None, description="Primary desire (e.g. Freedom, Scale)")
    decision_maker: Optional[DecisionMaker] = Field(None, description="Who makes the buying decision")
    
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

