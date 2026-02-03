import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.db.models.business import Product, JourneyProgress
from src.services.db.models.lead import Lead
from src.core.domain.offer_enums import OfferType, DeliveryModel, GuaranteeType, OfferStatus
from src.core.domain.lead_enums import FinancialCapacity, LeadTemperature, AvatarPersona
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/visionarias_logs")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 Starting Visionarias Data Seeding...")
        
        # 1. Update Products (Offers)
        products = db.query(Product).all()
        for p in products:
            print(f"Updating Product: {p.name}")
            
            # Default Values for Visionarias High Ticket Context
            if not p.type or p.type == "program": 
                p.type = OfferType.HYBRID_MENTORSHIP
            
            if not p.delivery_model:
                p.delivery_model = DeliveryModel.DWY # Do With You
                
            if not p.headline_promise:
                p.headline_promise = "Estructura, Lanza y Escala tu Negocio Digital High Ticket en 90 días sin sacrificar tu vida."
                
            if not p.target_avatar_match:
                p.target_avatar_match = [AvatarPersona.THE_VIP, AvatarPersona.THE_SKEPTIC]
                
            if not p.pricing or p.pricing == {}:
                p.pricing = [
                    {
                        "label": "Pago Único (Ahorras $1000)",
                        "total_amount": 2997.0,
                        "number_of_installments": 1,
                        "is_default": True,
                        "savings_claim": "Ahorras $1000 vs financiado"
                    },
                    {
                        "label": "Plan Flexible",
                        "total_amount": 3997.0,
                        "deposit_required": 997.0,
                        "installment_amount": 1000.0,
                        "number_of_installments": 3,
                        "is_default": False
                    }
                ]
                p.currency = "USD"
                
            if not p.guarantee_type:
                p.guarantee_type = GuaranteeType.CONDITIONAL_ACTION_BASED
                
            if not p.min_financial_capacity:
                p.min_financial_capacity = FinancialCapacity.STABLE_PROFESSIONAL
                
            if not p.internal_sku:
                p.internal_sku = f"VIS-{p.name.upper().replace(' ', '-')[:10]}"
                
        # 2. Update Leads
        leads = db.query(Lead).all()
        for l in leads:
            if not l.temperature:
                l.temperature = LeadTemperature.COLD
            
            # Initialize profile data structure if needed
            if not l.profile_data:
                l.profile_data = {}
                
        # 3. Update Journeys
        journeys = db.query(JourneyProgress).all()
        for j in journeys:
            if not j.product_line:
                # Infer from product type (simplified logic)
                j.product_line = "High Ticket"
            
            if not j.deal_value_potential:
                j.deal_value_potential = 2997.0 # Default pipeline value
                
        db.commit()
        print("✅ Data Seeding Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
