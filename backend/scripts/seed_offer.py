import sys
import os
from sqlalchemy.orm import sessionmaker

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.database import engine
from src.services.db.models.business import Product
from src.services.db.models.tenant import Tenant

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()
    try:
        # 1. Get a Tenant (Create one if not exists)
        tenant = db.query(Tenant).first()
        if not tenant:
            print("Creating default tenant...")
            tenant = Tenant(name="Default Tenant", slug="default")
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        
        print(f"Using Tenant: {tenant.name} ({tenant.id})")

        # 2. Define Offer Data
        offer_data = {
            "internal_sku": "TEST-001",
            "name": "Programa de Prueba (High Ticket)",
            "type": "COHORT_PROGRAM",
            "delivery_model": "DWY",
            "headline_promise": "Transforma tu negocio en 90 días con nuestro sistema probado de ventas automatizadas.",
            "target_avatar_match": ["Emprendedores Digitales", "Coaches", "Consultores"],
            "primary_outcome": "Sistema de ventas instalado y generando leads cualificados.",
            "time_to_value": "14 días para primeras ventas",
            "requires_application": True,
            "min_financial_capacity": "$2000 USD/mes disponible para inversión",
            "prerequisites": ["Tener una oferta validada", "Web básica"],
            "pricing": [
                {
                    "label": "Pago Único",
                    "total_amount": 2997,
                    "deposit_required": 500,
                    "number_of_installments": 1,
                    "installment_amount": 0,
                    "is_default": True,
                    "savings_claim": "Ahorra $500 vs Plan de Pagos"
                },
                {
                    "label": "Plan de Pagos",
                    "total_amount": 3500,
                    "deposit_required": 500,
                    "number_of_installments": 3,
                    "installment_amount": 1000,
                    "is_default": False
                }
            ],
            "currency": "USD",
            "guarantee_type": "CONDITIONAL_ACTION_BASED",
            "guarantee_terms": "Si implementas todo y no recuperas tu inversión, trabajamos contigo gratis hasta que lo logres.",
            "includes_offers": [],
            "deliverables": [
                {
                    "name": "Sesiones Grupales Semanales",
                    "format": "LIVE_CALL",
                    "quantity": "12",
                    "value_stack_price": 1997
                },
                {
                    "name": "Portal de Contenidos",
                    "format": "RECORDED_CONTENT",
                    "quantity": "Acceso de por vida",
                    "value_stack_price": 997
                }
            ],
            "status": "DRAFT",
            "specific_details": {
                "program_type": "COHORT_BASED",
                "duration_weeks": 12,
                "syllabus_modules": { "1": "Fundamentos", "2": "Estrategia", "3": "Implementación" },
                "calls_per_week": 2,
                "call_schedule_details": "Martes y Jueves 10 AM EST",
                "are_calls_recorded": True,
                "one_on_one_sessions": 3,
                "includes_certification": True
            },
            "tenant_id": tenant.id
        }

        # 3. Insert Offer
        # Check if exists by SKU to avoid duplicates
        existing = db.query(Product).filter(Product.internal_sku == offer_data["internal_sku"], Product.tenant_id == tenant.id).first()
        if existing:
            print(f"Offer with SKU {offer_data['internal_sku']} already exists. ID: {existing.id}")
        else:
            new_offer = Product(**offer_data)
            db.add(new_offer)
            db.commit()
            db.refresh(new_offer)
            print(f"✅ Created Offer: {new_offer.name} | ID: {new_offer.id}")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
