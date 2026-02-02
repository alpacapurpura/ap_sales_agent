from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class BrandIdentity(BaseModel):
    """
    Datos duros que dan legalidad y estructura a la empresa.
    """
    brand_name: Optional[str] = Field(None, description="Nombre comercial público")
    legal_name: Optional[str] = Field(None, description="Razón Social / Legal")
    website: Optional[str] = Field(None, description="Sitio Web Principal")
    industry: Optional[str] = Field(None, description="Industria / Nicho")
    logo_url: Optional[str] = Field(None, description="URL del logo de la empresa")
    timezone: Optional[str] = Field(None, description="Zona Horaria Base (IANA)")
    language: Optional[str] = Field("Español", description="Idioma Principal")

class KeyFigure(BaseModel):
    """
    Persona clave en la empresa (The Authority Squad).
    """
    id: str = Field(..., description="Unique ID for UI handling")
    name: str = Field(..., description="Nombre Completo")
    role: Optional[str] = Field(None, description="Rol / Título")
    is_primary_voice: bool = Field(False, description="¿Es la Voz Principal?")
    bio: Optional[str] = Field(None, description="Bio Corta (Hook)")
    gender: Optional[Literal["Masculino", "Femenino", "Neutro"]] = Field(None, description="Género")
    communication_style: Optional[str] = Field(None, description="Estilo de Comunicación")
    
    # Redes y Contacto
    personal_website: Optional[str] = Field(None, description="Website Personal URL")
    personal_linkedin: Optional[str] = Field(None, description="LinkedIn Personal URL")
    personal_instagram: Optional[str] = Field(None, description="Instagram Personal URL")
    personal_tiktok: Optional[str] = Field(None, description="TikTok Personal URL")
    personal_facebook: Optional[str] = Field(None, description="Facebook Personal URL")
    work_whatsapp: Optional[str] = Field(None, description="Whatsapp Trabajo")

class AuthorityItem(BaseModel):
    """
    Respaldo Institucional (Authority Vault).
    """
    id: str = Field(..., description="Unique ID for UI handling")
    entity_name: str = Field(..., description="Nombre de Entidad (Forbes, etc.)")
    type: Optional[str] = Field(None, description="Tipo de Respaldo")
    context: Optional[str] = Field(None, description="Contexto del Logro")
    proof_url: Optional[str] = Field(None, description="URL de Prueba")
    logo_url: Optional[str] = Field(None, description="Logo de la Entidad")

class ContactData(BaseModel):
    """
    Datos de Contacto.
    """
    support_email: Optional[str] = Field(None, description="Email de Soporte")
    phone: Optional[str] = Field(None, description="Teléfono Oficial")
    address: Optional[str] = Field(None, description="Dirección Física / Sede")
    social_instagram: Optional[str] = Field(None, description="Instagram URL")
    social_linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    social_youtube: Optional[str] = Field(None, description="YouTube URL")
    testimonials_url: Optional[str] = Field(None, description="Link Global de Testimonios")

class BrandSettings(BaseModel):
    """
    Configuración Global de Marca (Brand Settings).
    Se guarda en Tenant.config_json['brand_settings'].
    """
    identity: BrandIdentity = Field(default_factory=BrandIdentity)
    team: List[KeyFigure] = Field(default_factory=list)
    authority_vault: List[AuthorityItem] = Field(default_factory=list)
    contact: ContactData = Field(default_factory=ContactData)
