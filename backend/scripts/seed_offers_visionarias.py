import sys
import os
import logging

# Add backend to path so imports work
sys.path.append("/app")
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.services.database import SessionLocal
from src.services.db.models.business import Product
from src.services.db.models.tenant import Tenant
from src.modules.offer.domain.enums import (
    OfferValueLevel, OfferDeliveryModel, GuaranteeType
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_offers():
    db = next(get_db())
    
    # 1. Get or Create Tenant "Visionarias"
    tenant_slug = "visionarias"
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    
    if not tenant:
        logger.info(f"Creating Tenant: {tenant_slug}")
        tenant = Tenant(
            name="Visionarias Latam",
            slug=tenant_slug,
            config_json={
                "brand_colors": {"primary": "#D4AF37", "secondary": "#000000"},
                "currency": "USD"
            }
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    else:
        logger.info(f"Found Tenant: {tenant.name} ({tenant.id})")

    tenant_id = tenant.id

    # 2. Define Offers Data
    offers_data = [
        # --- N0: FREE RESOURCE ---
        {
            "internal_sku": "VIS-N0-MIND-GUIDE",
            "name": "Guía: Liberar la Mente",
            "archetype": "producto",
            "offer_value_level": OfferValueLevel.LEAD_MAGNET.value,
            "delivery_model": OfferDeliveryModel.DIY.value,
            "headline_promise": "Descubre cómo calmar tu mente para expandir tu visión.",
            "primary_outcome": "Claridad mental y reducción de ansiedad.",
            "time_to_value": "Inmediato",
            "pricing": [
                {
                    "label": "Gratis",
                    "plan_type": "one_time",
                    "total_amount": 0.0,
                    "is_default": True
                }
            ],
            "specific_details": {
                "format": "video",
                "file_type": "PDF",
                "download_limit": 5
            },
            "guarantee_type": "none" # It's free
        },
        
        # --- N1: TRIPWIRE ---
        {
            "internal_sku": "VIS-N1-MEDITATION-PACK",
            "name": "Pack Meditaciones: Abundancia",
            "archetype": "producto",
            "offer_value_level": OfferValueLevel.ACTIVACION.value,
            "delivery_model": OfferDeliveryModel.DIY.value,
            "headline_promise": "7 audios guiados para reprogramar tu mente hacia la abundancia.",
            "primary_outcome": "Mindset de abundancia activado.",
            "time_to_value": "7 días",
            "pricing": [
                {
                    "label": "Oferta Especial",
                    "plan_type": "one_time",
                    "total_amount": 27.0,
                    "savings_claim": "Ahorras $70",
                    "is_default": True
                }
            ],
            "specific_details": {
                "format": "video",
                "is_bundle": True,
                "file_type": "MP3"
            },
            "guarantee_type": "unconditional_30_day",
            "guarantee_terms": "7 días de garantía incondicional."
        },

        # --- N2: GROUP COACHING (CORE) ---
        {
            "internal_sku": "VIS-N2-PURPOSE-PROSPERITY",
            "name": "Programa: De Propósito a Prosperidad",
            "archetype": "programa",
            "offer_value_level": OfferValueLevel.TRANSFORMACION.value,
            "delivery_model": OfferDeliveryModel.DWY.value,
            "headline_promise": "8 semanas para transformar tu negocio en una marca auténtica y rentable.",
            "primary_outcome": "Negocio estructurado y facturando.",
            "time_to_value": "8 semanas",
            "pricing": [
                {
                    "label": "Pago Único",
                    "plan_type": "one_time",
                    "total_amount": 997.0,
                    "is_default": True
                },
                {
                    "label": "3 Cuotas",
                    "plan_type": "payment_plan",
                    "total_amount": 1197.0,
                    "number_of_installments": 3,
                    "installment_amount": 399.0,
                    "is_default": False
                }
            ],
            "specific_details": {
                "duration_weeks": 8,
                "calls_per_week": 1,
                "call_schedule_details": "Jueves 7PM EST",
                "includes_certification": True,
                "syllabus_modules": {
                    "1": "Mentalidad y Propósito",
                    "2": "Avatar y Oferta",
                    "3": "Marketing Orgánico",
                    "4": "Ventas"
                }
            },
            "guarantee_type": "conditional_action_based",
            "guarantee_terms": "Si implementas todo y no ves resultados, te devolvemos tu dinero."
        },

        # --- N3: 1:1 MENTORING ---
        {
            "internal_sku": "VIS-N3-VIP-VISION",
            "name": "Mentoría Privada: Visión Clara",
            "archetype": "servicio",
            "offer_value_level": OfferValueLevel.TRANSFORMACION.value,
            "delivery_model": OfferDeliveryModel.DWY.value,
            "headline_promise": "Acompañamiento estratégico 1 a 1 para escalar tu facturación.",
            "primary_outcome": "Escalabilidad y delegación.",
            "time_to_value": "3 meses",
            "pricing": [
                {
                    "label": "Inversión Total",
                    "plan_type": "one_time",
                    "total_amount": 3000.0,
                    "is_default": True
                }
            ],
            "specific_details": {
                "max_concurrent_clients": 5,
                "onboarding_timeline": "Auditoría inicial en 48h",
                "communication_channels": ["WhatsApp", "Zoom"],
                "deliverables_list": ["Plan de 90 días", "Soporte diario", "Revisión de funnels"]
            },
            "guarantee_type": "none"
        },

        # --- N4: DFY AGENCY ---
        {
            "internal_sku": "VIS-N4-AGENCY-DFY",
            "name": "Agencia Visionarias DFY",
            "archetype": "servicio",
            "offer_value_level": OfferValueLevel.TRANSFORMACION.value,
            "delivery_model": OfferDeliveryModel.DFY.value,
            "headline_promise": "Nosotras construimos tu ecosistema digital mientras tú te enfocas en tu genio.",
            "primary_outcome": "Funnel de ventas automatizado y funcionando.",
            "time_to_value": "30 días",
            "pricing": [
                {
                    "label": "Setup Fee + Retainer",
                    "plan_type": "one_time",
                    "total_amount": 5000.0,
                    "is_default": True
                }
            ],
            "specific_details": {
                "max_concurrent_clients": 3,
                "deliverables_list": ["Diseño Web", "Copywriting", "Automatización Email", "Setup Ads"],
                "onboarding_timeline": "Kickoff Call inmediata",
                "account_manager_assigned": True
            },
            "guarantee_type": "conditional_action_based"
        },

        # --- N6: CORPORATE (B2B) ---
        {
            "internal_sku": "VIS-N6-CORP-TRAINING",
            "name": "Visionarias Corporate Leadership",
            "archetype": "experiencia",
            "offer_value_level": OfferValueLevel.CORPORATIVO.value,
            "delivery_model": "hybrid",
            "headline_promise": "Capacitación de liderazgo femenino para empresas Fortune 500.",
            "primary_outcome": "Líderes empoderadas y cultura inclusiva.",
            "time_to_value": "Custom",
            "pricing": [
                {
                    "label": "Cotización a Medida",
                    "plan_type": "one_time",
                    "total_amount": 15000.0,
                    "is_default": True
                }
            ],
            "specific_details": {
                "location_type": "physical_local",
                "max_attendees": 50,
                "start_date": "2026-06-01", # Future date
                "end_date": "2026-06-03",
                "itinerary_summary": "3 días de inmersión en liderazgo y bienestar corporativo."
            },
            "guarantee_type": "none"
        }
    ]

    # 3. Upsert Offers
    for offer_data in offers_data:
        # Check if exists by SKU
        existing_offer = db.query(Product).filter(
            Product.internal_sku == offer_data["internal_sku"],
            Product.tenant_id == tenant_id
        ).first()

        if existing_offer:
            logger.info(f"Updating Offer: {offer_data['name']}")
            for key, value in offer_data.items():
                setattr(existing_offer, key, value)
        else:
            logger.info(f"Creating Offer: {offer_data['name']}")
            new_offer = Product(**offer_data)
            new_offer.tenant_id = tenant_id
            new_offer.status = "active" # Set default status
            new_offer.currency = "USD"
            db.add(new_offer)
    
    db.commit()
    logger.info("Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_offers()
