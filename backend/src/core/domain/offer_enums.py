from enum import Enum
from typing import Dict, Any, List, Optional

# --- 1. CORE HIERARCHY ---

class OfferValueLevel(str, Enum):
    """
    Define el nivel de valor y precio promedio. Clasifica la oferta desde contenido gratuito
    hasta servicios corporativos.
    """
    N0 = "N0"  # ADQUISICIÓN Y AUTORIDAD (GRATIS)
    N1 = "N1"  # ACTIVACIÓN (LOW TICKET)
    N2 = "N2"  # TRANSFORMACIÓN ESCALABLE (MID-HIGH TICKET)
    N3 = "N3"  # INTENSIDAD Y EXCLUSIVIDAD (HIGH TICKET 1:1)
    N4 = "N4"  # DELEGACIÓN Y EJECUCIÓN (AGENCIA / DFY)
    N5 = "N5"  # ESTATUS Y ENTORNO (ULTRA HIGH TICKET)
    N6 = "N6"  # CORPORATIVO Y MARCA (B2B)

class OfferDeliveryModel(str, Enum):
    """
    Define cómo se estructura y ejecuta la entrega de valor.
    """
    DIY = "DIY"  # Do It Yourself - Hazlo Tú Mismo
    DWY = "DWY"  # Do It With You - Hazlo Contigo
    DFY = "DFY"  # Do It For You - Lo Hago Por Ti
    B2B = "B2B"  # Business To Business - Transformamos empresas

class OfferType(str, Enum):
    """
    Taxonomía de Productos y Servicios. Organiza las ofertas desde la adquisición gratuita
    hasta la venta corporativa.
    """
    # NIVEL 0
    FREE_RESOURCE = "FREE_RESOURCE"
    COMMUNITY_LITE = "COMMUNITY_LITE"
    CONTENT_ASSET_PODCAST = "CONTENT_ASSET_PODCAST"
    
    # NIVEL 0/1 (Webinar can be both)
    FREE_WEBINAR_CHALLENGE = "FREE_WEBINAR_CHALLENGE"

    # NIVEL 1
    TRIPWIRE_OFFER = "TRIPWIRE_OFFER"
    SELF_PACED_COURSE = "SELF_PACED_COURSE"
    PAID_NEWSLETTER_SUBSCRIPTION = "PAID_NEWSLETTER_SUBSCRIPTION"
    PHYSICAL_MERCH = "PHYSICAL_MERCH" # NEW: Added for physical products

    # NIVEL 2
    HYBRID_MENTORSHIP = "HYBRID_MENTORSHIP"
    COHORT_BASED_COURSE = "COHORT_BASED_COURSE"
    GROUP_COACHING_PROGRAM = "GROUP_COACHING_PROGRAM"

    # NIVEL 3
    VIP_DAY_STRATEGY = "VIP_DAY_STRATEGY"
    ONE_ON_ONE_PRIVATE_MENTORING = "1ON1_PRIVATE_MENTORING"
    DEEP_DIVE_AUDIT = "DEEP_DIVE_AUDIT"

    # NIVEL 4
    PRODUCTIZED_SERVICE = "PRODUCTIZED_SERVICE"
    MONTHLY_RETAINER = "MONTHLY_RETAINER"
    PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE"

    # NIVEL 5
    MASTERMIND_NETWORK = "MASTERMIND_NETWORK"
    LUXURY_RETREAT = "LUXURY_RETREAT"

    # NIVEL 6
    CORPORATE_TRAINING = "CORPORATE_TRAINING"
    BRAND_SPONSORSHIP = "BRAND_SPONSORSHIP"
    KEYNOTE_SPEAKING = "KEYNOTE_SPEAKING"

# --- 2. TACTICAL ENUMS ---

class FulfillmentType(str, Enum):
    """
    Define la logística de entrega. CRÍTICO para el Agente IA.
    Le dice al Agente qué pedirle al usuario (Email vs Dirección Física).
    """
    DIRECT_DOWNLOAD = "DIRECT_DOWNLOAD"
    # El archivo se entrega directamente (ej. PDF en email o página de gracias).
    
    EXTERNAL_PLATFORM_ACCESS = "EXTERNAL_PLATFORM"
    # Se entrega acceso a un LMS (Kajabi, Hotmart, Notion). Requiere crear usuario.
    
    PHYSICAL_SHIPPING = "PHYSICAL_SHIPPING"
    # Requiere logística de paquetería. El Agente DEBE pedir dirección y teléfono.

class DigitalFormat(str, Enum):
    """
    Formato técnico del entregable. Ayuda a manejar expectativas.
    """
    PDF_DOCUMENT = "PDF"
    VIDEO_FILE = "MP4/MOV"
    AUDIO_FILE = "MP3"
    SPREADSHEET = "XLS/CSV"
    NOTION_TEMPLATE = "NOTION"
    ZIP_BUNDLE = "ZIP"
    SAAS_ACCESS = "SAAS_KEY" # Licencias de software.
    PHYSICAL_ITEM = "PHYSICAL" # Para cuando no es digital.

class ProgramStructure(str, Enum):
    """
    Define la rigidez temporal del programa.
    Instruye a la IA sobre cómo vender la 'Urgencia' y el 'Inicio'.
    """
    FIXED_DATE_COHORT = "FIXED_COHORT"
    # "Empezamos todos juntos el 1 de Marzo y terminamos el 30 de Abril". (Urgencia Máxima).
    
    ROLLING_ADMISSION = "ROLLING_EVERGREEN"
    # "Entra cuando quieras, tienes 12 semanas de soporte desde tu pago". (Venta constante).
    
    CHALLENGE_SPRINT = "CHALLENGE"
    # "Intensivo de 3-5 días para lograr un resultado micro". (Alto volumen, baja duración).

class LiveInteractionType(str, Enum):
    """
    Define el nivel de acceso al experto. Clave para justificar el precio (High Ticket).
    """
    GROUP_Q_AND_A = "GROUP_Q&A" # Preguntas y respuestas masivas.
    WORKSHOP_PRACTICAL = "WORKSHOP" # "Hot Seats" o trabajo práctico en vivo.
    LIVE_PROGRAM_DELIVERY = "LIVE_PROGRAM_DELIVERY" # Programa dictado en vivo.
    HYBRID_SUPPORT = "HYBRID" # Clases grabadas + Sesiones en vivo de soporte.
    NO_LIVE_COMPONENTS = "ASYNC_ONLY" # Solo comunidad escrita, sin Zoom.

class CommunityPlatform(str, Enum):
    """
    Dónde ocurre la magia de la interacción.
    """
    WHATSAPP_TELEGRAM = "CHAT_APP" # Común en Retos (Challenges).
    FACEBOOK_GROUP = "FB_GROUP" # Clásico, pero en desuso para High Ticket.
    CIRCLE_SKOOL = "DEDICATED_PLATFORM" # El estándar moderno (Skool, Circle, Mighty).
    DISCORD_SLACK = "CHAT_SERVER" # Para nichos más técnicos o B2B.
    ZOOM = "ZOOM"
    GOOGLE_MEETS = "GOOGLE_MEETS"
    NONE = "NONE"

class ServiceCategory(str, Enum):
    """
    Define la naturaleza operativa del servicio.
    INSTRUCCIÓN IA: Usa esto para saber 'quién trabaja' y 'qué se entrega'.
    """
    ADVISORY_CONSULTING = "ADVISORY"
    # "Yo te digo cómo hacerlo". (Mentoría 1:1, Auditoría, VIP Day, Strategy Call).
    # Foco: Agenda y Conocimiento.
    
    DONE_FOR_YOU_AGENCY = "EXECUTION_AGENCY"
    # "Yo lo hago por ti". (Edición de video, Funnels, Copywriting, Gestión de Ads).
    # Foco: Entregables y Tiempos (SLA).
    
    B2B_AUTHORITY_RENTAL = "AUTHORITY_RENTAL"
    # "Yo te presto mi audiencia/imagen". (Podcast Ads, UGC, Speaker, Embajadora de marca).
    # Foco: Alcance y Derechos de uso.

class InteractionMode(str, Enum):
    """
    Define cómo interactúan el proveedor y el cliente.
    INSTRUCCIÓN IA: Define si bloquear calendario o esperar un email.
    """
    SYNCHRONOUS_LIVE = "SYNC_LIVE"
    # Requiere coincidir en el tiempo (Zoom, Presencial).
    
    ASYNC_DELIVERY = "ASYNC_DELIVERY"
    # Sin reuniones. Se entrega por email/drive (Ej. Auditoría grabada, Edición de video).
    
    HYBRID_MODEL = "HYBRID"
    # Kickoff en vivo + Ejecución asíncrona (Ej. Mentoría con seguimiento por WhatsApp).

class ServiceFrequency(str, Enum):
    """
    Define la recurrencia del compromiso.
    """
    ONE_OFF_PROJECT = "ONE_OFF" # Proyecto de inicio y fin (Ej. Crear una web, VIP Day).
    RETAINER_RECURRING = "RETAINER" # Pago mensual por servicio continuo (Ej. Community Management).
    PACK_OF_SESSIONS = "PACK" # Paquete finito (Ej. Bono de 4 sesiones).

class GuaranteeType(str, Enum):
    """
    Estrategia de Risk Reversal.
    """
    UNCONDITIONAL_X_DAY = "UNCONDITIONAL_X_DAY"
    CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED"
    EXCHANGE_ONLY = "EXCHANGE_ONLY"
    NO_REFUNDS = "NO_REFUNDS"

class OfferStatus(str, Enum):
    """
    Disponibilidad para generar ESCASEZ o URGENCIA.
    """
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

    # Legacy / Variantes de Disponibilidad
    ALWAYS_ON = "ALWAYS_ON"
    LAUNCH_WINDOW_CLOSING = "LAUNCH_WINDOW"
    WAITLIST_ONLY = "WAITLIST_ONLY"
    SOLD_OUT = "SOLD_OUT"

class DeliverableFormat(str, Enum):
    """
    Qué recibe exactamente el cliente.
    """
    LIVE_GROUP_CALL = "LIVE_GROUP_CALL"
    ONE_ON_ONE_CALL = "1ON1_CALL"
    RECORDED_CONTENT = "RECORDED_CONTENT"
    PHYSICAL_SHIPMENT = "PHYSICAL_SHIPMENT"
    DFY_ASSET = "DFY_ASSET"

class EventLocationType(str, Enum):
    """
    Ubicación para eventos y retiros.
    """
    VIRTUAL_REMOTE = "VIRTUAL"
    IN_PERSON_LOCAL = "IN_PERSON_LOCAL"
    DESTINATION_RETREAT = "DESTINATION_RETREAT"

class AccommodationType(str, Enum):
    """
    Tipo de alojamiento para retiros.
    """
    NOT_INCLUDED = "NOT_INCLUDED"
    SHARED_ROOM = "SHARED_ROOM"
    PRIVATE_ROOM = "PRIVATE_ROOM"
    LUXURY_SUITE = "LUXURY_SUITE"

class PaymentPlanType(str, Enum):
    """
    Estrategia de negociación financiera.
    """
    PAY_IN_FULL = "PAY_IN_FULL"
    INTERNAL_SPLIT_PAY = "SPLIT_PAY"
    THIRD_PARTY_FINANCE = "3RD_PARTY"
    SUBSCRIPTION_RECURRING = "SUBSCRIPTION"

class AccessDuration(str, Enum):
    """
    Vida útil del servicio.
    """
    LIFETIME_CONTENT = "LIFETIME"
    LIMITED_TIME_ACCESS = "LIMITED_TIME"
    DURATION_OF_PAYMENT = "PAY_TO_PLAY"
    HYBRID_ACCESS = "HYBRID_ACCESS"

class PrerequisiteType(str, Enum):
    """
    Criterios de filtrado (Gating).
    """
    NO_PREREQUISITE = "NONE"
    GENDER_IDENTITY = "GENDER_IDENTITY"
    REVENUE_LEVEL = "REVENUE_LEVEL"
    BUSINESS_STAGE = "BUSINESS_STAGE"

class OnboardingMechanism(str, Enum):
    """
    Call to Action final.
    """
    CHECKOUT_LINK = "SEND_LINK"
    CALENDAR_BOOKING = "BOOK_CALL"
    INTAKE_FORM = "INTAKE_FORM"
    COMMUNITY_INVITE = "JOIN_COMMUNITY"

class BillingFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"

# --- 3. METADATA REGISTRY ---

# Rich metadata for UI hints and AI understanding
OFFER_METADATA: Dict[str, Dict[str, Any]] = {
    # --- LEVEL 0 ---
    OfferType.FREE_RESOURCE.value: {
        "level": OfferValueLevel.N0,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Recursos Descargables Gratuitos",
        "hint": "Ebook, plantillas o checklists. Intercambio de valor por contacto.",
        "description": "Cualquier recurso de consumo rápido cuyo objetivo es la captura de datos."
    },
    OfferType.COMMUNITY_LITE.value: {
        "level": OfferValueLevel.N0,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Comunidad Lite / Nutrición",
        "hint": "Grupo de Telegram/WhatsApp gratuito.",
        "description": "Soporte mínimo, enfocado en nutrir leads y prueba social."
    },
    OfferType.FREE_WEBINAR_CHALLENGE.value: {
        "level": OfferValueLevel.N0,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Evento en Vivo / Lanzamiento",
        "hint": "Masterclass o Reto de 3-5 días.",
        "description": "Generan urgencia y educan para posicionar la oferta superior."
    },
    OfferType.CONTENT_ASSET_PODCAST.value: {
        "level": OfferValueLevel.N0,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Activo de Contenido Principal",
        "hint": "Podcast o canal de YouTube.",
        "description": "Nutrición de leads fríos B2C y autoridad a largo plazo."
    },
    # --- LEVEL 1 ---
    OfferType.TRIPWIRE_OFFER.value: {
        "level": OfferValueLevel.N1,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Oferta Tripwire",
        "hint": "Oferta irresistible de bajo costo ($7-$97).",
        "description": "Autofinancia la publicidad. Alto valor percibido."
    },
    OfferType.SELF_PACED_COURSE.value: {
        "level": OfferValueLevel.N1,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Curso Auto-dirigido",
        "hint": "Curso grabado sin soporte en vivo.",
        "description": "El cliente lo consume a su ritmo. Escalabilidad infinita."
    },
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION.value: {
        "level": OfferValueLevel.N1,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Suscripción Premium",
        "hint": "Contenido exclusivo recurrente (Substack).",
        "description": "Membresía de bajo costo para fomentar compromiso."
    },
    OfferType.PHYSICAL_MERCH.value: {
        "level": OfferValueLevel.N1,
        "default_delivery": OfferDeliveryModel.DIY,
        "label": "Merchandising / Producto Físico",
        "hint": "Ropa, libros, accesorios.",
        "description": "Productos físicos que requieren envío."
    },
    # --- LEVEL 2 ---
    OfferType.HYBRID_MENTORSHIP.value: {
        "level": OfferValueLevel.N2,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Mentoría Híbrida",
        "hint": "El 'Gold Standard'. Curso + Q&A semanal.",
        "description": "Eficiencia y soporte grupal. Rentabilidad masiva."
    },
    OfferType.COHORT_BASED_COURSE.value: {
        "level": OfferValueLevel.N2,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Curso por Cohortes",
        "hint": "Curso en vivo con fecha de inicio/fin.",
        "description": "Usa urgencia y responsabilidad grupal."
    },
    OfferType.GROUP_COACHING_PROGRAM.value: {
        "level": OfferValueLevel.N2,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Coaching Grupal",
        "hint": "Facilitación en vivo, menos contenido grabado.",
        "description": "Centrado en desbloqueo e implementación."
    },
    # --- LEVEL 3 ---
    OfferType.VIP_DAY_STRATEGY.value: {
        "level": OfferValueLevel.N3,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "VIP Day / Strategy Day",
        "hint": "4-8 horas intensivas 1:1.",
        "description": "Resolver un problema específico con plan inmediato."
    },
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING.value: {
        "level": OfferValueLevel.N3,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Mentoría Privada 1:1",
        "hint": "Acompañamiento largo plazo (3-6 meses).",
        "description": "Máxima personalización para transformación profunda."
    },
    OfferType.DEEP_DIVE_AUDIT.value: {
        "level": OfferValueLevel.N3,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Auditoría Profunda",
        "hint": "Análisis exhaustivo + Plan de Acción.",
        "description": "No solo diagnóstico, sino ruta de implementación."
    },
    # --- LEVEL 4 ---
    OfferType.PRODUCTIZED_SERVICE.value: {
        "level": OfferValueLevel.N4,
        "default_delivery": OfferDeliveryModel.DFY,
        "label": "Servicio Productizado",
        "hint": "Servicio 'empaquetado' de pago único.",
        "description": "Alcance fijo (ej. 'Te monto el funnel')."
    },
    OfferType.MONTHLY_RETAINER.value: {
        "level": OfferValueLevel.N4,
        "default_delivery": OfferDeliveryModel.DFY,
        "label": "Retainer Mensual",
        "hint": "Pago recurrente por gestión continua.",
        "description": "Ingresos predecibles (Ads, Redes, Edición)."
    },
    OfferType.PERFORMANCE_REV_SHARE.value: {
        "level": OfferValueLevel.N4,
        "default_delivery": OfferDeliveryModel.DFY,
        "label": "Partnership por Resultados",
        "hint": "Cobro base bajo + % de resultados.",
        "description": "Modelo Growth Partner."
    },
    # --- LEVEL 5 ---
    OfferType.MASTERMIND_NETWORK.value: {
        "level": OfferValueLevel.N5,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Red de Mastermind",
        "hint": "Acceso a 'La Habitación' y conexiones.",
        "description": "Valor en networking y peer-to-peer coaching."
    },
    OfferType.LUXURY_RETREAT.value: {
        "level": OfferValueLevel.N5,
        "default_delivery": OfferDeliveryModel.DWY,
        "label": "Retiro Inmersivo",
        "hint": "Experiencia de 3-4 días (Viaje + Negocios).",
        "description": "Conexión profunda fuera del entorno habitual."
    },
    # --- LEVEL 6 ---
    OfferType.CORPORATE_TRAINING.value: {
        "level": OfferValueLevel.N6,
        "default_delivery": OfferDeliveryModel.B2B,
        "label": "Capacitación Corporativa",
        "hint": "Venta a departamentos de RRHH.",
        "description": "Capacitación in-company."
    },
    OfferType.BRAND_SPONSORSHIP.value: {
        "level": OfferValueLevel.N6,
        "default_delivery": OfferDeliveryModel.B2B,
        "label": "Patrocinios",
        "hint": "Venta de acceso a la audiencia.",
        "description": "Publicidad nativa en activos de contenido."
    },
    OfferType.KEYNOTE_SPEAKING.value: {
        "level": OfferValueLevel.N6,
        "default_delivery": OfferDeliveryModel.B2B,
        "label": "Conferencias / Keynotes",
        "hint": "Ponencias pagadas en eventos.",
        "description": "Monetización de reputación y autoridad."
    }
}

# --- OTHER METADATA REGISTRIES (Examples) ---
GUARANTEE_METADATA = {
    GuaranteeType.UNCONDITIONAL_X_DAY.value: {
        "hint": "Ideal para N1 y N2. Elimina fricción total.",
        "description": "Tienes X días. Si no te encanta, te devolvemos el dinero."
    },
    GuaranteeType.CONDITIONAL_ACTION_BASED.value: {
        "hint": "Ideal para N3. Exige compromiso del cliente.",
        "description": "Si completas el trabajo y no ves resultados, te devolvemos el dinero."
    },
    GuaranteeType.EXCHANGE_ONLY.value: {
        "hint": "Para N1 Merch o productos físicos.",
        "description": "Solo cambios de talla/producto, no dinero."
    },
    GuaranteeType.NO_REFUNDS.value: {
        "hint": "Estricto para N4 Eventos/DFY y N5 B2B.",
        "description": "Venta final sin devolución."
    }
}

def get_enum_options(enum_class: Any, metadata_registry: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Helper to serialize Enums for Frontend Select components.
    Includes rich metadata if available.
    """
    options = []
    for member in enum_class:
        item = {
            "value": member.value,
            "label": member.name.replace("_", " ").title(), # Fallback label
            "description": member.__doc__ or ""
        }
        
        # Override with rich metadata if exists
        if metadata_registry and member.value in metadata_registry:
            meta = metadata_registry[member.value]
            item.update(meta)
        
        options.append(item)
    return options
