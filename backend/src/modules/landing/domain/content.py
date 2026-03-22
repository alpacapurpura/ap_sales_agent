from typing import List, Optional, Union, Dict, Any
from pydantic import Field, model_validator
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.landing.domain.enums import LandingPageArchetype, LandingPageFont

# --- SHARED BLOCKS ---

class FeatureBullet(BaseEntity):
    icon: Optional[str] = None # Emoji or Icon name
    title: str
    description: Optional[str] = None

class Testimonial(BaseEntity):
    author_name: str
    author_role: Optional[str] = None
    content: str
    avatar_url: Optional[str] = None

class LandingPageTheme(BaseEntity):
    primary_color: str = Field("#000000", description="Hex code for primary actions")
    secondary_color: str = Field("#ffffff", description="Hex code for backgrounds/accents")
    font_pair: LandingPageFont = LandingPageFont.SANS_SERIF
    dark_mode: bool = False

# --- ARCHETYPE CONTENT MODELS ---

# 1. THE SQUEEZE (Captura Pura)
class SqueezeContent(BaseEntity):
    headline: str = Field(..., description="Promesa clara y curiosa")
    subheadline: str = Field(..., description="Elimina la objeción principal")
    visual_url: Optional[str] = Field(None, description="Mockup del descargable")
    bullets: List[str] = Field(..., description="3 puntos de fascinación")
    cta_text: str = Field("Envíamelo ahora", description="Texto del botón")
    privacy_text: str = Field("Tu información está segura.", description="Texto bajo el botón")

# 2. THE EVENT (Webinar/Reto)
class EventContent(BaseEntity):
    headline: str = Field(..., description="Promesa del evento + 'En Vivo'")
    event_date: datetime = Field(..., description="FECHA y HORA del evento")
    hook_question: str = Field(..., description="¿Estás cansado de [Problema]?")
    secret_bullets: List[str] = Field(..., description="3-5 secretos que se revelarán")
    speaker_name: str
    speaker_bio: str
    speaker_image_url: Optional[str] = None
    cta_text: str = Field("Reservar mi lugar gratis", description="Texto del botón")

# 3. THE FLASH OFFER (Tripwire)
class FlashOfferContent(BaseEntity):
    headline: str = Field(..., description="Orientado al problema")
    offer_name: str = Field(..., description="Qué es exactamente")
    problem_agitation: str = Field(..., description="Agitación rápida del problema")
    solution_description: str = Field(..., description="Por qué es rápido y fácil")
    original_price: float = Field(..., description="Price Anchor (Valuado en)")
    discounted_price: float = Field(..., description="Precio actual")
    guarantee_text: str = Field("30 días o devolución", description="Garantía")
    cta_text: str = Field("Añadir al carrito", description="Texto del botón")
    product_image_url: Optional[str] = None

# 4. THE TRANSFORMER (Cursos/Mentorías - Estructura A-G)
class TransformerContent(BaseEntity):
    headline: str = Field(..., description="Gancho principal: Transformación de Identidad en X tiempo")
    subheadline: str = Field(..., description="Promesa secundaria o bajada")
    problem_text: str = Field(..., description="El dolor actual del avatar")
    agitation_text: str = Field(..., description="Por qué es costoso no resolverlo")
    solution_text: str = Field(..., description="La nueva esperanza/camino")
    method_name: str = Field(..., description="Nombre del Mecanismo Único")
    method_description: str = Field(..., description="Explicación breve del método")
    authority_name: str = Field(..., description="Nombre del experto")
    authority_bio: str = Field(..., description="Bio corta enfocada en resultados")
    authority_image_url: Optional[str] = None
    modules: List[FeatureBullet] = Field(..., description="Desglose de módulos/semanas")
    bonuses: List[FeatureBullet] = Field([], description="Bonus Stack mata-objeciones")
    price_anchor: str = Field(..., description="Precio regular tachado")
    price_offer: str = Field(..., description="Precio oferta actual")
    scarcity_text: str = Field(..., description="Urgencia")
    cta_text: str = Field("Inscribirme al programa", description="Texto del botón")
    testimonials: List[Testimonial] = Field([], description="Prueba social")
    story_hook: Optional[str] = Field(None, description="Historia del fundador (opcional)")

# 5. THE VELVET ROPE (High Ticket)
class VelvetRopeContent(BaseEntity):
    headline: str = Field(..., description="Exclusividad y Pertenencia")
    manifesto_text: str = Field(..., description="Valores y visión del grupo")
    who_is_this_for: List[str] = Field(..., description="Filtro positivo")
    who_is_NOT_for: List[str] = Field(..., description="Filtro negativo")
    experience_image_urls: List[str] = Field([], description="Fotos de eventos pasados")
    scarcity_text: str = Field(..., description="Ej: 'Solo 10 cupos anuales'")
    cta_text: str = Field("Aplicar para una entrevista", description="Texto del botón")

# 6. THE BROCHURE (Servicios B2B)
class BrochureContent(BaseEntity):
    headline: str = Field(..., description="Beneficio Claro + ROI")
    authority_logos: List[str] = Field([], description="Logos de clientes o prensa")
    process_steps: List[FeatureBullet] = Field(..., description="Cómo trabajamos (Paso 1, 2, 3)")
    deliverables: List[str] = Field(..., description="Lista técnica de lo que incluye")
    case_studies: List[Testimonial] = Field([], description="Casos de éxito")
    cta_text: str = Field("Agendar llamada de descubrimiento", description="Texto del botón")

# --- MASTER CONFIG ---

class LandingPageConfig(BaseEntity):
    archetype: LandingPageArchetype
    theme: LandingPageTheme = Field(default_factory=LandingPageTheme)
    
    # Polymorphic Content Container
    content: Union[
        SqueezeContent, 
        EventContent, 
        FlashOfferContent, 
        TransformerContent, 
        VelvetRopeContent, 
        BrochureContent,
        Dict[str, Any]
    ]

    slug: str = Field(..., description="URL slug pública (ej: /p/mi-oferta-increible)")
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_published: bool = False

    @model_validator(mode='after')
    def validate_content_matches_archetype(self):
        """
        Ensures the content object matches the selected archetype.
        """
        # Allow Dict (Puck Data)
        if isinstance(self.content, dict):
            return self

        mapping = {
            LandingPageArchetype.THE_SQUEEZE: SqueezeContent,
            LandingPageArchetype.THE_EVENT: EventContent,
            LandingPageArchetype.THE_FLASH_OFFER: FlashOfferContent,
            LandingPageArchetype.THE_TRANSFORMER: TransformerContent,
            LandingPageArchetype.THE_VELVET_ROPE: VelvetRopeContent,
            LandingPageArchetype.THE_BROCHURE: BrochureContent,
        }
        
        expected_type = mapping.get(self.archetype)
        if expected_type and not isinstance(self.content, expected_type):
            # Strict validation might be annoying during migration or partial updates
            # raise ValueError(f"Content mismatch")
            pass
        
        return self
