from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import uuid

class BrandIdentity(BaseModel):
    """
    Datos duros que dan legalidad y estructura a la empresa.
    """
    brand_name: Optional[str] = Field(None, description="Nombre comercial público")
    legal_name: Optional[str] = Field(None, description="Razón Social / Legal")
    tax_id: Optional[str] = Field(None, description="Identificación Fiscal (RUC/RFC/NIT)")
    fiscal_address: Optional[str] = Field(None, description="Dirección Fiscal")
    website: Optional[str] = Field(None, description="Sitio Web Principal")
    industry: Optional[str] = Field(None, description="Industria / Nicho")
    logo_url: Optional[str] = Field(None, description="URL del logo de la empresa")
    timezone: Optional[str] = Field(None, description="Zona Horaria Base (IANA)")
    language: Optional[str] = Field("Español", description="Idioma Principal")
    
    # --- New Identity Fields ---
    tagline: Optional[str] = Field(None, description="Slogan o frase comercial corta")
    description: Optional[str] = Field(None, description="Descripción corta (Elevator Pitch)")
    founding_year: Optional[str] = Field(None, description="Año de fundación")
    
    # --- New Legal Fields ---
    legal_representative: Optional[str] = Field(None, description="Nombre del Representante Legal")
    terms_url: Optional[str] = Field(None, description="Enlace a Términos y Condiciones")
    privacy_url: Optional[str] = Field(None, description="Enlace a Política de Privacidad")

class BrandStoryMilestone(BaseModel):
    """
    Hito en la historia de la marca.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    year: str = Field(..., description="Año o Fecha")
    title: str = Field(..., description="Título del Hito")
    description: Optional[str] = Field(None, description="Descripción corta")

class BrandStory(BaseModel):
    """
    El Origen y la Historia (Storytelling).
    """
    origin_story: Optional[str] = Field(None, description="La historia del origen (El 'Por qué')")
    milestones: List[BrandStoryMilestone] = Field(default_factory=list, description="Línea de tiempo")

class BrandCompetitor(BaseModel):
    """
    Competencia Directa/Indirecta.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    name: str = Field(..., description="Nombre del Competidor")
    differentiation: Optional[str] = Field(None, description="¿Por qué somos diferentes?")

class BrandLogos(BaseModel):
    """
    Kit de Logos de la Marca.
    """
    primary: Optional[str] = Field(None, description="Logo Principal (Completo)")
    secondary: Optional[str] = Field(None, description="Logo Secundario (Icono/Simbolo)")
    dark_mode: Optional[str] = Field(None, description="Logo para fondos oscuros (Blanco/Claro)")
    light_mode: Optional[str] = Field(None, description="Logo para fondos claros (Negro/Oscuro)")

class BrandMethodologyPillar(BaseModel):
    """
    Pilar de la Metodología.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    title: str = Field(..., description="Nombre del Pilar/Fase")
    description: Optional[str] = Field(None, description="Explicación")

class BrandStrategy(BaseModel):
    """
    Estrategia de Marca (Competencia, UVP, Metodología).
    """
    unique_value_proposition: Optional[str] = Field(None, description="Propuesta de Valor Única (UVP)")
    competitors: List[BrandCompetitor] = Field(default_factory=list, description="Análisis de Competencia")
    methodology_name: Optional[str] = Field(None, description="Nombre del Método (ej: 'Método 4C')")
    methodology_description: Optional[str] = Field(None, description="Descripción General del Método")
    methodology_pillars: List[BrandMethodologyPillar] = Field(default_factory=list, description="Pilares del Método")

class KeyFigure(BaseModel):
    """
    Persona clave en la empresa (The Authority Squad).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for UI handling")
    name: str = Field(..., description="Nombre Completo")
    role: Optional[str] = Field(None, description="Rol / Título")
    is_primary_voice: bool = Field(False, description="¿Es la Voz Principal?")
    bio: Optional[str] = Field(None, description="Bio Corta (Hook)")
    gender: Optional[Literal["Masculino", "Femenino", "Neutro"]] = Field(None, description="Género")
    communication_style: Optional[str] = Field(None, description="Estilo de Comunicación")
    headshot_url: Optional[str] = Field(None, description="URL de la foto de perfil")
    gallery: List[str] = Field(default_factory=list, description="Galería personal de imágenes")
    
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for UI handling")
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
    sales_email: Optional[str] = Field(None, description="Email de Ventas")
    phone: Optional[str] = Field(None, description="Teléfono Oficial")
    whatsapp: Optional[str] = Field(None, description="WhatsApp Business Oficial")
    address: Optional[str] = Field(None, description="Dirección Física / Sede")
    social_instagram: Optional[str] = Field(None, description="Instagram URL")
    social_linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    social_youtube: Optional[str] = Field(None, description="YouTube URL")
    social_tiktok: Optional[str] = Field(None, description="TikTok URL")
    social_facebook: Optional[str] = Field(None, description="Facebook URL")
    social_twitter: Optional[str] = Field(None, description="X / Twitter URL")
    testimonials_url: Optional[str] = Field(None, description="Link Global de Testimonios")

class BrandVisuals(BaseModel):
    """
    Identidad Visual (Colores, Tipografía, Estilo).
    """
    primary_color: str = Field("#0f172a", description="Color Primario (Hex) - Default Slate 900")
    accent_color: str = Field("#3b82f6", description="Color Acento (Hex) - Default Blue 500")
    font_heading: str = Field("Inter", description="Fuente de Títulos")
    font_body: str = Field("Inter", description="Fuente de Cuerpo")
    style_preset: Optional[str] = Field(None, description="ID del Kit usado (ej: 'corporate')")
    
    # --- Brand Assets ---
    logos: BrandLogos = Field(default_factory=BrandLogos, description="Kit de Logos")

    # --- Extended Palette ---
    background_color: Optional[str] = Field("#FFFFFF", description="Color de fondo principal")
    text_primary_color: Optional[str] = Field("#000000", description="Color de texto principal")
    text_on_primary: Optional[str] = Field("#FFFFFF", description="Color de texto sobre primario")
    
    # --- Context & Rules ---
    design_style: Optional[str] = Field(None, description="Descripción del estilo de diseño")
    usage_guidelines: List[str] = Field(default_factory=list, description="Guías de uso inferidas")

class TestimonialItem(BaseModel):
    """
    Testimonio de Cliente (Social Proof).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    type: Literal["text", "video"] = Field("text", description="Tipo de testimonio")
    content: str = Field(..., description="Texto del testimonio o URL del video")
    author_name: str = Field(..., description="Nombre del autor")
    author_role: Optional[str] = Field(None, description="Rol o Empresa del autor")
    author_avatar: Optional[str] = Field(None, description="URL del avatar del autor")
    rating: Optional[int] = Field(5, description="Calificación (1-5)")

class BrandSettings(BaseModel):
    """
    Configuración Global de Marca (Brand Settings).
    Se guarda en Tenant.config_json['brand_settings'].
    """
    identity: BrandIdentity = Field(default_factory=BrandIdentity)
    story: BrandStory = Field(default_factory=BrandStory)
    strategy: BrandStrategy = Field(default_factory=BrandStrategy)
    visuals: BrandVisuals = Field(default_factory=BrandVisuals)
    team: List[KeyFigure] = Field(default_factory=list)
    testimonials: List[TestimonialItem] = Field(default_factory=list)
    authority_vault: List[AuthorityItem] = Field(default_factory=list)
    contact: ContactData = Field(default_factory=ContactData)
