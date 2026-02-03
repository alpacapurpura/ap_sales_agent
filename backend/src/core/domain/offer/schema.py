from typing import List, Optional, Union, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from src.core.domain.offer_enums import (
    OfferType, DeliveryModel, GuaranteeType, OfferStatus, DeliverableFormat,
    ProductFormat, ServiceCapacity, ProgramType, BillingFrequency,
    PaymentPlanType, AccessDuration, PrerequisiteType, OnboardingMechanism
)
from src.core.domain.lead_enums import FinancialCapacity, AvatarPersona

# --- SPECIFIC DETAILS SCHEMAS ---

class ProductDetails(BaseModel):
    format: ProductFormat
    is_bundle: bool = False
    file_type: Optional[str] = None
    access_link: Optional[str] = None
    download_limit: Optional[int] = None
    stock_quantity: int = 0
    shipping_zones: List[str] = []
    shipping_cost: float = 0.0
    estimated_delivery_days: str = "3-5 días hábiles"
    bulk_discount_threshold: Optional[int] = None

class ServiceDetails(BaseModel):
    capacity_status: ServiceCapacity
    max_concurrent_clients: int
    current_active_clients: int = 0
    deliverables_list: List[str]
    excluded_services: List[str] = []
    onboarding_timeline: str
    min_contract_months: int = 1
    account_manager_assigned: bool = False
    communication_channels: List[str] = ["Email"]

class ProgramDetails(BaseModel):
    program_type: ProgramType
    duration_weeks: int
    syllabus_modules: Dict[int, str]
    calls_per_week: int
    call_schedule_details: str
    are_calls_recorded: bool = True
    one_on_one_sessions: int = 0
    start_date: Optional[str] = None # ISO Date string
    enrollment_deadline: Optional[str] = None # ISO Date string
    includes_certification: bool = False
    requirements_to_graduate: str = ""

class SubscriptionDetails(BaseModel):
    billing_cycle: BillingFrequency
    trial_period_days: int = 0
    tier_name: str
    platform_name: str
    cancellation_policy: str
    save_offer_script: str
    content_update_freq: str
    expert_guests: bool = False
    networking_events: bool = False

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
    savings_claim: Optional[str] = None

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
    delivery_model: DeliveryModel
    
    # --- 2. THE PROMISE ---
    headline_promise: str
    target_avatar_match: List[AvatarPersona]
    primary_outcome: str
    time_to_value: str
    
    # --- 2.1 ACCESS & DURATION ---
    access_duration: Optional[AccessDuration] = Field(None, description="Define por cuánto tiempo tienen acceso al contenido (Ej: Lifetime vs 1 año).")
    support_duration_days: Optional[int] = Field(None, description="Días calendario de soporte humano/técnico incluido (Distinto al acceso al contenido).")
    
    # --- 3. GATEKEEPING ---
    requires_application: bool
    min_financial_capacity: FinancialCapacity
    prerequisites: List[Union[PrerequisiteType, str]] = Field([], description="Lista de barreras de entrada obligatorias.")
    anti_avatar_keywords: List[str] = Field([], description="Palabras clave (Negative Persona) que, si se detectan, activan descalificación inmediata (Ej: 'gratis', 'barato').")
    
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
    onboarding_url: Optional[str] = Field(None, description="La URL destino (Thank You Page o Calendario) para ejecutar la acción.")
    
    # --- 7. ASSETS ---
    vsl_link: Optional[str] = None
    checkout_page_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    
    status: OfferStatus
    
    # --- 8. POLYMORPHIC DETAILS ---
    specific_details: Optional[Union[ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails]] = None

# Alias for backward compatibility
HighTicketOffer = Offer
