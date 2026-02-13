from typing import List, Optional, Union, Dict, Type
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, HttpUrl
from src.core.domain.offer_enums import (
    OfferType, OfferDeliveryModel, GuaranteeType, OfferStatus, DeliverableFormat,
    OfferValueLevel, PaymentPlanType, AccessDuration, PrerequisiteType, OnboardingMechanism,
    EventLocationType, BillingFrequency, OFFER_METADATA, FulfillmentType, DigitalFormat,
    ProgramStructure, LiveInteractionType, CommunityPlatform, ServiceCategory, InteractionMode, ServiceFrequency,
    AccommodationType
)
from src.core.domain.lead_enums import FinancialCapacity, AvatarPersona
from src.core.domain.landing_page.schema import LandingPageConfig

# --- SPECIFIC DETAILS SCHEMAS ---

class SessionDetails(BaseModel):
    """
    Detalle de una sesión recurrente o evento clave del programa.
    """
    title: str = Field(..., description="Nombre de la sesión (ej. 'Mentoria Q&A', 'Clase Maestra')")
    day_of_week: str = Field(..., description="Día de la semana (Lunes, Martes, etc.)")
    time: str = Field(..., description="Hora de inicio (Formato HH:MM)")
    duration_minutes: int = Field(60, description="Duración en minutos")

class ProductDetails(BaseModel):
    """
    CONFIGURATION SCHEMA FOR: Static Assets (DIY & Merch).
    Este esquema contiene toda la lógica necesaria para entregar un producto
    sin intervención humana síncrona.
    """

    # ==============================================================================
    # 1. LÓGICA DE ENTREGA (FULFILLMENT LOGIC)
    # ==============================================================================
    fulfillment_type: Optional[FulfillmentType] = Field(
        None,
        description="DETERMINA EL FLUJO POST-COMPRA. Si es PHYSICAL, activa recolección de dirección."
    )

    access_url: Optional[HttpUrl] = Field(
        None,
        description="LA LLAVE DEL REINO. Si es Digital, este es el link de descarga, el link de Notion o el acceso a Kajabi. Si es Físico, puede estar vacío."
    )

    access_instructions: Optional[str] = Field(
        None,
        description="El 'Copy' del email de entrega. Ej: 'Haz clic en duplicar en tu Notion' o 'Tus credenciales llegarán en otro correo'."
    )

    # ==============================================================================
    # 2. ATRIBUTOS DEL PRODUCTO (PRODUCT SPECS)
    # ==============================================================================
    format: Optional[DigitalFormat] = Field(
        None,
        description="Formato del archivo o ítem. Usado para mostrar íconos en el Dashboard (ej. Icono de PDF vs Video)."
    )

    is_downloadable: bool = Field(
        True,
        description="True = El usuario se queda el archivo (PDF). False = Solo consumo en línea (Curso en Video protegido)."
    )

    estimated_consumption_time_minutes: Optional[int] = Field(
        None,
        description="Valor percibido. Ej: 60 (para un video de 1h) o 15 (para leer un PDF). Ayuda a vender la 'facilidad'."
    )

    # ==============================================================================
    # 3. LOGÍSTICA FÍSICA (SOLO PARA MERCH / LIBROS)
    # ==============================================================================
    requires_shipping: bool = Field(
        False,
        description="FLAG MAESTRA. Si es True, el Checkout DEBE pedir: Address, City, Zip, Country."
    )

    sku_inventory_code: Optional[str] = Field(
        None,
        description="Identificador de inventario interno. Ej: 'HOODIE-VIS-M'. Necesario para integración con almacén."
    )

    stock_quantity: Optional[int] = Field(
        None,
        description="Inventario disponible. Si llega a 0, el Agente debe marcar la oferta como 'SOLD_OUT' o 'WAITLIST'."
    )

    shipping_weight_grams: Optional[int] = Field(
        None,
        description="Peso para cálculo de tarifas de envío. Opcional pero recomendado para e-commerce."
    )

    # ==============================================================================
    # 4. VALIDACIÓN DE LÓGICA DE NEGOCIO (AI GUARDRAILS)
    # ==============================================================================
    @model_validator(mode='after')
    def validate_fulfillment_logic(self):
        """
        Reglas de consistencia lógica.
        Nota: Se permite faltar datos para soportar borradores (DRAFT).
        La validación de completitud se hace en el Frontend (Flight Check).
        """
        # Regla 3: Coherencia de formato (Siempre aplicable).
        if self.format == DigitalFormat.PHYSICAL_ITEM and self.fulfillment_type != FulfillmentType.PHYSICAL_SHIPPING:
            raise ValueError("Format is PHYSICAL but fulfillment is set to Digital.")

        return self

class ServiceDetails(BaseModel):
    """
    SCHEMA DE CONFIGURACIÓN: Servicios Profesionales, Agencia y B2B.
    Contiene la lógica de agendas, entregables, contratos y especificaciones técnicas.
    """

    # --- A. CLASIFICACIÓN MACRO ---
    category: Optional[ServiceCategory] = Field(
        None,
        description="El clasificador maestro. Determina si el usuario compra TIEMPO (Advisory), TRABAJO (Agency) o IMPACTO (Authority)."
    )
    
    interaction_mode: Optional[InteractionMode] = Field(
        None,
        description="Modalidad de entrega. Si es SYNC, exige link de agenda. Si es ASYNC, exige formulario de input."
    )

    frequency_type: Optional[ServiceFrequency] = Field(
        None,
        description="Si es RETAINER, la IA debe hablar de 'mensualidad' y 'compromiso mínimo'."
    )

    # --- B. DEFINICIÓN DEL ALCANCE (SCOPE OF WORK) ---
    deliverables_list: List[str] = Field(
        default_factory=list,
        description="Lista explícita de lo que incluye. Ej: ['Auditoría SEO en PDF', '4 Videos Verticales', 'Mención de 60s']. CRÍTICO para evitar 'Scope Creep' (que el cliente pida de más)."
    )

    revision_rounds: int = Field(
        0,
        description="Número de cambios permitidos. 0 = Sin cambios. Usado típicamente en Agencia (Diseño/Video)."
    )

    # --- C. LOGÍSTICA DE TIEMPO Y AGENDA (SOLO ADVISORY & HYBRID) ---
    booking_url: Optional[HttpUrl] = Field(
        None,
        description="Link a Calendly/Cal.com. OBLIGATORIO si 'interaction_mode' es SYNC o HYBRID. Es la 'Next Best Action' post-pago."
    )

    session_duration_minutes: Optional[int] = Field(
        None,
        description="Duración por sesión. Ej: 60, 90. Ayuda a la IA a gestionar expectativas de tiempo."
    )

    total_sessions_count: Optional[int] = Field(
        None,
        description="Total de sesiones en el paquete. Si es None en un Retainer, implica sesiones ilimitadas o según necesidad."
    )

    # --- D. LOGÍSTICA DE EJECUCIÓN (SOLO AGENCY & RETAINERS) ---
    turnaround_time_days: Optional[int] = Field(
        None,
        description="SLA (Acuerdo de Nivel de Servicio). 'Entregamos el primer borrador en X días hábiles'. La IA usa esto para calmar la ansiedad del cliente."
    )

    onboarding_brief_url: Optional[HttpUrl] = Field(
        None,
        description="Link al Formulario de Inicio (Typeform/Tally). Para Agencia, el servicio NO arranca sin esto. La IA debe perseguir este llenado."
    )

    min_contract_months: Optional[int] = Field(
        None,
        description="Permanencia mínima. Si es un Retainer de Agencia, la IA debe avisar: 'Recuerda que el contrato es por mínimo 3 meses'."
    )

    # --- E. ESPECIFICACIONES B2B & PATROCINIOS (SOLO AUTHORITY) ---
    # Esto es vital para 'Influencers de Nicho' que venden publicidad.
    
    audience_reach_metric: Optional[str] = Field(
        None,
        description="Dato de autoridad para venta B2B. Ej: 'Newsletter con 15k Open Rate' o 'Podcast con 5k descargas/sem'. La IA usa esto para cerrar tratos con marcas."
    )

    technical_requirements: Optional[str] = Field(
        None,
        description="Qué necesitamos de la marca. Ej: 'Logo en vectores y Guion de 100 palabras'. La IA debe solicitar esto en el onboarding B2B."
    )

    usage_rights_description: Optional[str] = Field(
        None,
        description="Derechos de uso del contenido (UGC). Ej: 'Uso orgánico por 12 meses, no Ads'. Evita problemas legales."
    )

    requires_contract_signature: bool = Field(
        False,
        description="Si True, la IA no debe dar por cerrado el trato solo con el pago, debe recordar firmar el PDF (Docusign/HelloSign)."
    )

    # ==============================================================================
    # 3. VALIDACIÓN DE LÓGICA DE NEGOCIO (AI GUARDRAILS)
    # ==============================================================================
    @model_validator(mode='after')
    def validate_service_consistency(self):
        """
        Reglas de negocio para consistencia (Integridad).
        La completitud se delega al Flight Check.
        """
        # REGLA 1: Si vendemos TIEMPO (Síncrono), y hay booking_url, debe ser válida.
        # (Relaxed: No exigimos booking_url para guardar borrador)
        
        # REGLA 2: Integridad de Agencia
        if self.category == ServiceCategory.DONE_FOR_YOU_AGENCY:
            if not self.turnaround_time_days and self.frequency_type == ServiceFrequency.ONE_OFF_PROJECT:
                 # Esta regla es de integridad, quizás mantener o relajar? 
                 # Relajamos para borrador.
                 pass

        # REGLA 3: Integridad B2B
        if self.category == ServiceCategory.B2B_AUTHORITY_RENTAL:
            # Relajamos requirements
            pass

        return self

class ProgramModule(BaseModel):
    """
    Un módulo educativo dentro de un programa.
    """
    title: str = Field(..., description="Título del Módulo (ej. 'Semana 1: Fundamentos')")
    description: Optional[str] = Field(None, description="Descripción corta o resultado de aprendizaje")
    topics: List[str] = Field(default_factory=list, description="Lista de temas o lecciones")

class ProgramDetails(BaseModel):
    """
    CONFIGURATION SCHEMA FOR: Transformational Programs (Cohorts & Mentorships).
    Este esquema contiene la lógica de calendario, capacidad y entrega de soporte.
    """

    # ==============================================================================
    # 0. CURRICULUM (NEW: EDUCATIONAL STRUCTURE)
    # ==============================================================================
    curriculum: List[ProgramModule] = Field(
        default_factory=list,
        description="Estructura educativa del programa (Módulos y Lecciones)."
    )

    # ==============================================================================
    # 1. ESTRUCTURA TEMPORAL (TIME & URGENCY)
    # ==============================================================================
    structure_type: Optional[ProgramStructure] = Field(
        None,
        description="El modelo de calendario. Determina si validamos fechas fijas o duración relativa."
    )

    start_date: Optional[datetime] = Field(
        None,
        description="OBLIGATORIO para FIXED_COHORT y CHALLENGE. La fecha de 'Kick-off'. La IA usa esto para cuentas regresivas ('Faltan 3 días')."
    )

    registration_end_date: Optional[datetime] = Field(
        None,
        description="Fecha límite para inscribirse. Si es None, se asume igual a start_date."
    )

    end_date: Optional[datetime] = Field(
        None,
        description="Fecha de graduación o cierre del grupo. Define el ciclo de vida de la cohorte."
    )

    is_end_date_estimated: bool = Field(
        False,
        description="Si True, la fecha de fin es tentativa."
    )

    duration_weeks: Optional[int] = Field(
        None,
        description="Duración total del compromiso. Ej: 12 semanas. Si es ROLLING, define cuánto tiempo tienen acceso al soporte."
    )

    # ==============================================================================
    # 2. CAPACIDAD Y ESCASEZ (SCARCITY ENGINE)
    # ==============================================================================
    cohort_limit: Optional[int] = Field(
        None,
        description="Límite duro de alumnos (Hard Cap). Si enrolled >= limit, la oferta pasa a WAITLIST automáticamente."
    )

    current_enrollment_count: int = Field(
        0,
        description="Contador en tiempo real. La IA debe leer esto para decir: 'Solo quedan X lugares'."
    )

    is_application_required: bool = Field(
        False,
        description="Si es True, el usuario no puede comprar directo. Debe agendar llamada o llenar form (High Ticket Gating)."
    )

    # ==============================================================================
    # 3. DINÁMICA DE ENTREGA (DELIVERY LOGIC)
    # ==============================================================================
    interaction_type: Optional[LiveInteractionType] = Field(
        None,
        description="Qué recibe el usuario en vivo. Vital para diferenciar un curso de $200 vs una mentoría de $2,000."
    )

    live_schedule_description: Optional[str] = Field(
        None,
        description="DEPRECATED: Usar 'schedule' para estructura. Texto legible para el humano. Ej: 'Jueves 7 PM Hora CDMX'."
    )

    schedule: List[SessionDetails] = Field(
        default_factory=list,
        description="Lista estructurada de sesiones recurrentes."
    )

    # Links de Acceso (El 'Dónde')
    lms_url: Optional[HttpUrl] = Field(
        None,
        description="Link a la plataforma educativa (Kajabi/Hotmart) donde están los videos grabados."
    )

    community_platform: CommunityPlatform = Field(
        CommunityPlatform.NONE,
        description="Plataforma de comunidad."
    )

    community_invite_link: Optional[HttpUrl] = Field(
        None,
        description="Link de invitación al grupo (Discord/WhatsApp). Se entrega post-compra."
    )

    # ==============================================================================
    # 4. CERTIFICACIÓN Y RESULTADOS
    # ==============================================================================
    has_certification: bool = Field(
        False,
        description="Si al finalizar se entrega un diploma/certificado. Aumenta el valor percibido (B2B/Career)."
    )

    homework_submission_required: bool = Field(
        False,
        description="Si el alumno debe entregar trabajos para avanzar. Implica carga operativa de corrección."
    )

    # ==============================================================================
    # 5. VALIDACIÓN DE LÓGICA DE NEGOCIO (AI GUARDRAILS)
    # ==============================================================================
    @model_validator(mode='after')
    def validate_program_logic(self):
        """
        Reglas temporales y de consistencia para programas educativos.
        Relaxed for Drafts.
        """
        # Regla 1: Coherencia de Fechas (Solo si ambas existen)
        if self.start_date and self.end_date:
             if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")

        return self

class SubscriptionDetails(BaseModel):
    """
    For N1/N4 Memberships and Retainers.
    """
    billing_cycle: BillingFrequency
    trial_period_days: int = 0
    tier_name: str
    platform_name: str
    cancellation_policy: str
    content_update_freq: str
    expert_guests: bool = False
    networking_events: bool = False

class EventDetails(BaseModel):
    """
    SCHEMA DE CONFIGURACIÓN: Eventos, Retiros y Masterminds.
    Maneja la logística de ubicación (física/virtual) y experiencia del asistente.
    """

    # ==============================================================================
    # 1. COORDENADAS TEMPORALES (TIME)
    # ==============================================================================
    start_date: Optional[datetime] = Field(
        None,
        description="Fecha y hora de inicio exacta."
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="Fecha y hora de fin exacta."
    )
    
    timezone: str = Field(
        "UTC",
        description="Zona horaria del evento (ej. 'America/Mexico_City'). CRÍTICO para eventos globales."
    )

    # ==============================================================================
    # 2. MOTOR DE UBICACIÓN (LOCATION ENGINE)
    # ==============================================================================
    location_type: Optional[EventLocationType] = Field(
        None,
        description="Define si es Virtual, Físico Local o Retiro en Destino."
    )

    # --- A. Lógica Virtual ---
    virtual_meeting_url: Optional[HttpUrl] = Field(
        None,
        description="Link de Zoom/YouTube. OBLIGATORIO si es VIRTUAL."
    )
    
    is_recorded: bool = Field(
        True,
        description="¿Se entrega grabación? Maneja la objeción 'No puedo asistir en vivo'."
    )

    # --- B. Lógica Física (Local & Retiro) ---
    venue_name: Optional[str] = Field(
        None,
        description="Nombre del Hotel o Lugar (ej. 'Hotel Hilton Reforma'). OBLIGATORIO si es Físico."
    )
    
    venue_address: Optional[str] = Field(
        None,
        description="Dirección completa para Google Maps."
    )
    
    map_link: Optional[HttpUrl] = Field(
        None,
        description="Link directo a Google Maps."
    )

    # ==============================================================================
    # 3. LOGÍSTICA DE VIAJE (SOLO RETIROS)
    # ==============================================================================
    accommodation_type: AccommodationType = Field(
        AccommodationType.NOT_INCLUDED,
        description="Nivel de hospedaje incluido en el ticket."
    )
    
    recommended_airport_code: Optional[str] = Field(
        None,
        description="Código IATA (ej. CUN) para vuelos. Ayuda al usuario a planear."
    )
    
    is_transfer_included: bool = Field(
        False,
        description="¿Incluye transporte Aeropuerto-Hotel?"
    )

    # ==============================================================================
    # 4. EXPERIENCIA DEL PARTICIPANTE
    # ==============================================================================
    agenda_highlights: List[str] = Field(
        default_factory=list,
        description="Puntos clave para vender la emoción (ej. 'Cena de Blanco', 'Yoga')."
    )
    
    dress_code: Optional[str] = Field(
        None,
        description="Código de vestimenta (ej. 'Formal de Playa')."
    )
    
    dietary_restrictions_form_url: Optional[HttpUrl] = Field(
        None,
        description="Link para registrar alergias alimenticias."
    )

    # ==============================================================================
    # 5. VALIDACIÓN DE LÓGICA DE NEGOCIO (AI GUARDRAILS)
    # ==============================================================================
    @model_validator(mode='after')
    def validate_event_logistics(self):
        """
        Reglas de consistencia para eventos físicos y virtuales.
        Relaxed for Drafts.
        """
        # REGLA 1: Coherencia Temporal (Solo si ambas existen)
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("Event end_date must be after start_date.")

        # REGLA 2: Coherencia Virtual
        if self.location_type == EventLocationType.VIRTUAL_REMOTE:
            if self.venue_address or self.venue_name:
                raise ValueError("Virtual events should not have a physical venue address/name.")
        
        # REGLA 3: Coherencia Física (Relaxed: No exigimos venue_name en borrador)
        
        return self

# --- POLYMORPHIC MAPPING ---

# ### AI INSTRUCTION: REGISTER NEW OFFER TYPES HERE ###
# When adding a new OfferType in offer_enums.py, you MUST map it to its corresponding
# details schema here. If a new Schema is needed, define it above first.
# This mapping is the SOURCE OF TRUTH for the validation logic.

OFFER_TYPE_TO_DETAILS_MAPPING: Dict[OfferType, Type[BaseModel]] = {
    # LEVEL 0
    OfferType.FREE_RESOURCE: ProductDetails,
    OfferType.COMMUNITY_LITE: SubscriptionDetails,
    OfferType.CONTENT_ASSET_PODCAST: ProductDetails,
    OfferType.FREE_WEBINAR_CHALLENGE: ProgramDetails, # UPDATED: Challenges are Programs

    # LEVEL 1
    OfferType.TRIPWIRE_OFFER: ProductDetails,
    OfferType.SELF_PACED_COURSE: ProductDetails,
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION: SubscriptionDetails,
    OfferType.PHYSICAL_MERCH: ProductDetails,

    # LEVEL 2
    OfferType.HYBRID_MENTORSHIP: ProgramDetails,
    OfferType.COHORT_BASED_COURSE: ProgramDetails,
    OfferType.GROUP_COACHING_PROGRAM: ProgramDetails,

    # LEVEL 3
    OfferType.VIP_DAY_STRATEGY: ServiceDetails,
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING: ServiceDetails,
    OfferType.DEEP_DIVE_AUDIT: ServiceDetails,

    # LEVEL 4
    OfferType.PRODUCTIZED_SERVICE: ServiceDetails,
    OfferType.MONTHLY_RETAINER: ServiceDetails,
    OfferType.PERFORMANCE_REV_SHARE: ServiceDetails,

    # LEVEL 5
    OfferType.MASTERMIND_NETWORK: EventDetails, # Often implies events/retreats
    OfferType.LUXURY_RETREAT: EventDetails,

    # LEVEL 6
    OfferType.CORPORATE_TRAINING: ServiceDetails,
    OfferType.BRAND_SPONSORSHIP: ServiceDetails,
    OfferType.KEYNOTE_SPEAKING: ServiceDetails,
}

# --- SHARED SCHEMAS ---

class PricingStructure(BaseModel):
    """
    El motor de negociación.
    """
    label: str = Field(..., description="e.g. 'Pago Único' or 'Plan Financiado'")
    plan_type: Optional[PaymentPlanType] = Field(None, description="Clasificación financiera del plan")
    total_amount: float
    deposit_required: float = 0.0
    number_of_installments: int = 1
    installment_amount: float = 0.0
    is_default: bool = False
    savings_claim: Optional[str] = None # "Ahorras $500 vs pago mensual"

class DeliverableItem(BaseModel):
    """
    Lo que incluye exactamente.
    """
    name: str
    format: DeliverableFormat
    quantity: str
    value_stack_price: float

class Offer(BaseModel):
    """
    La Entidad Oferta Maestra con Detalles Polimórficos.
    """
    # --- 1. IDENTIFICATION ---
    id: Optional[UUID] = None
    internal_sku: str
    public_name: str
    type: OfferType
    
    # Auto-filled if not provided, based on type
    value_level: Optional[OfferValueLevel] = Field(None, validation_alias="offer_value_level")
    delivery_model: Optional[OfferDeliveryModel] = None
    
    # --- 2. THE PROMISE ---
    headline_promise: str
    target_avatar_match: List[AvatarPersona]
    primary_outcome: str
    time_to_value: str
    
    # --- 2.1 ACCESS & DURATION ---
    access_duration: Optional[AccessDuration] = Field(None, description="Define por cuánto tiempo tienen acceso al contenido (Ej: Lifetime vs 1 año).")
    access_duration_text: Optional[str] = Field(None, description="Texto libre para especificar la duración (ej. '1 Año', '6 Meses').")
    support_duration_days: Optional[int] = Field(None, description="Días calendario de soporte humano/técnico incluido.")
    instructors: List[str] = Field(default_factory=list, description="IDs de los mentores (KeyFigures)")
    
    # --- 3. GATEKEEPING ---
    requires_application: bool
    min_financial_capacity: FinancialCapacity
    prerequisites: List[Union[PrerequisiteType, str]] = Field([], description="Lista de barreras de entrada obligatorias.")
    anti_avatar_keywords: List[str] = Field([], description="Palabras clave (Negative Persona) que activan descalificación.")
    
    # --- 4. FINANCIAL ARCHITECTURE ---
    pricing_options: List[PricingStructure]
    price_pay_in_full: Optional[float] = Field(None, description="Precio con descuento por pago contado (Anchor Price real).")
    currency: str = "USD"
    
    # --- 5. RISK & GUARANTEE ---
    guarantee_type: GuaranteeType
    guarantee_terms: str
    
    # --- 6. RELATIONSHIPS ---
    downsell_offer_id: Optional[UUID] = None
    upsell_offer_id: Optional[UUID] = None
    includes_offers: List[UUID] = [] # Modularization support
    deliverables: List[DeliverableItem] = []

    # --- 6.1 ONBOARDING ---
    onboarding_action: Optional[OnboardingMechanism] = Field(None, description="La acción técnica a ejecutar tras el éxito del pago.")
    onboarding_url: Optional[str] = Field(None, description="La URL destino (Thank You Page o Calendario).")
    
    # --- 7. ASSETS ---
    vsl_link: Optional[str] = None
    checkout_page_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    
    status: OfferStatus
    
    # --- 8. POLYMORPHIC DETAILS ---
    specific_details: Optional[Union[ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails]] = None

    # --- 9. LANDING PAGE ENGINE ---
    landing_page_config: Optional[LandingPageConfig] = Field(None, description="Configuración de la Landing Page generada por IA")

    @model_validator(mode='after')
    def validate_consistency(self):
        """
        Ensures logical consistency across the Offer model:
        1. Auto-fills defaults from metadata if missing.
        2. STRICTLY validates that value_level matches the OfferType definition.
        3. STRICTLY validates that specific_details matches the OfferType mapping.
        """
        if not self.type:
            return self

        # --- METADATA LOOKUP ---
        meta = OFFER_METADATA.get(self.type.value, {})
        expected_level = meta.get("level")
        default_delivery = meta.get("default_delivery")

        # --- 1. VALUE LEVEL VALIDATION ---
        if self.value_level is None:
            # Auto-fill
            self.value_level = expected_level
        elif expected_level and self.value_level != expected_level:
            # Strict Validation: Prevent contradictions
            raise ValueError(
                f"Consistency Error: OfferType '{self.type.name}' implies Value Level '{expected_level.name}', "
                f"but got '{self.value_level.name}'. Please fix the Level or change the Type."
            )

        # --- 2. DELIVERY MODEL VALIDATION ---
        if self.delivery_model is None:
            # Auto-fill
            self.delivery_model = default_delivery
        # Note: We do NOT enforce strict delivery model equality because some types 
        # might validly pivot (e.g. a Workshop can be DWY or DIY).
        
        # --- 3. POLYMORPHIC DETAIL VALIDATION ---
        expected_detail_class = OFFER_TYPE_TO_DETAILS_MAPPING.get(self.type)
        
        if expected_detail_class:
            # If details are missing, we could auto-init empty, but validation implies they should be provided if required.
            # For now, if provided, MUST match.
            if self.specific_details is not None:
                if not isinstance(self.specific_details, expected_detail_class):
                    raise ValueError(
                        f"Polymorphism Error: OfferType '{self.type.name}' requires details of type '{expected_detail_class.__name__}', "
                        f"but got '{type(self.specific_details).__name__}'."
                    )
            # Optional: Enforce presence? 
            # if self.specific_details is None:
            #     raise ValueError(f"OfferType '{self.type.name}' requires specific_details ({expected_detail_class.__name__})")

        return self

# Alias for backward compatibility
HighTicketOffer = Offer
