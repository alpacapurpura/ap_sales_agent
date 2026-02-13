import sys
import os
import uuid
import logging
from datetime import datetime

# Add backend to path so imports work
sys.path.append("/app")
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.services.database import SessionLocal
from src.services.db.models.business import Product
from src.services.db.models.tenant import Tenant
from src.core.domain.offer_enums import (
    OfferType, OfferValueLevel, OfferDeliveryModel, 
    DeliverableFormat, PaymentPlanType, EventLocationType, 
    GuaranteeType
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

def seed_n5_offers():
    db = next(get_db())
    
    # 1. Get Tenant "Visionarias"
    tenant_slug = "visionarias"
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    
    if not tenant:
        logger.error(f"Tenant {tenant_slug} not found. Please run the main seed script first.")
        return

    tenant_id = tenant.id
    logger.info(f"Seeding N5 Offers for Tenant: {tenant.name} ({tenant.id})")

    # 2. Define N5 Offers Data
    offers_data = [
        # --- N5: MASTERMIND NETWORK ---
        {
            "internal_sku": "VIS-N5-MASTERMIND-ELITE",
            "name": "Círculo Visionarias Elite",
            "type": OfferType.MASTERMIND_NETWORK.value,
            "offer_value_level": OfferValueLevel.N5.value,
            "delivery_model": OfferDeliveryModel.DWY.value,
            "headline_promise": "Acceso exclusivo a la red de mujeres empresarias más influyentes de Latam.",
            "primary_outcome": "Networking de alto nivel y alianzas estratégicas.",
            "time_to_value": "Inmediato al ingresar",
            "pricing": [
                {
                    "label": "Membresía Anual",
                    "plan_type": PaymentPlanType.PAY_IN_FULL.value,
                    "total_amount": 12000.0,
                    "is_default": True
                },
                {
                    "label": "Pago Trimestral",
                    "plan_type": PaymentPlanType.SUBSCRIPTION_RECURRING.value,
                    "total_amount": 14000.0,
                    "number_of_installments": 4,
                    "installment_amount": 3500.0,
                    "is_default": False
                }
            ],
            "specific_details": {
                "max_attendees": 20,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "location_type": EventLocationType.VIRTUAL_REMOTE.value,
                "itinerary_summary": "Reuniones mensuales de consejo, acceso a directorio y eventos privados.",
                "networking_events": True,
                "expert_guests": True
            },
            "guarantee_type": GuaranteeType.NO_REFUNDS.value
        },
        
        # --- N5: LUXURY RETREAT ---
        {
            "internal_sku": "VIS-N5-RETREAT-TULUM",
            "name": "Retiro Visionarias: Tulum 2026",
            "type": OfferType.LUXURY_RETREAT.value,
            "offer_value_level": OfferValueLevel.N5.value,
            "delivery_model": OfferDeliveryModel.DWY.value,
            "headline_promise": "4 días de desconexión, lujo y expansión de consciencia en el paraíso.",
            "primary_outcome": "Renovación energética y claridad de visión.",
            "time_to_value": "4 días",
            "pricing": [
                {
                    "label": "All Inclusive",
                    "plan_type": PaymentPlanType.PAY_IN_FULL.value,
                    "total_amount": 5500.0,
                    "is_default": True
                }
            ],
            "specific_details": {
                "location_type": EventLocationType.DESTINATION_RETREAT.value,
                "venue_address": "Azulik Tulum, Mexico",
                "start_date": "2026-11-10",
                "end_date": "2026-11-14",
                "max_attendees": 12,
                "accommodation_included": True,
                "meals_included": True,
                "itinerary_summary": "Yoga al amanecer, talleres de estrategia, cenas gourmet y tiempo libre."
            },
            "guarantee_type": GuaranteeType.NO_REFUNDS.value
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
    logger.info("N5 Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_n5_offers()
