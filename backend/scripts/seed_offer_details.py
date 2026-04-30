import os
import random
import sys
from datetime import datetime, timedelta

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.db.models.business import Product

# Database Connection (Adjust URL if needed, assuming default dev container)
DATABASE_URL = "postgresql://postgres:password@localhost:5432/visionarias_logs"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_dummy_details(archetype: str):
    """Generates dummy specific_details based on archetype."""

    if archetype == "producto":
        return {
            "fulfillment_type": "DIRECT_DOWNLOAD",
            "access_url": "https://example.com/download",
            "format": "PDF",
            "is_downloadable": True,
            "requires_shipping": False,
        }

    if archetype == "programa":
        return {
            "structure_type": "FIXED_COHORT",
            "start_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "duration_weeks": 12,
            "cohort_limit": 50,
            "current_enrollment_count": random.randint(0, 20),
            "interaction_type": "GROUP_Q&A",
            "live_schedule_description": "Jueves 7 PM Hora CDMX",
            "community_platform": "DEDICATED_PLATFORM",
            "community_invite_link": "https://skool.com/community",
        }

    if archetype == "servicio":
        return {
            "category": "ADVISORY",
            "interaction_mode": "SYNC_LIVE",
            "frequency_type": "ONE_OFF",
            "deliverables_list": ["Auditoría PDF", "Plan de Acción", "Grabación de Sesión"],
            "booking_url": "https://calendly.com/expert/vip-day",
        }

    if archetype == "membresia":
        return {
            "billing_cycle": "MONTHLY",
            "tier_name": "Pro Member",
            "platform_name": "Skool",
            "cancellation_policy": "Cancel anytime",
            "content_update_freq": "Weekly",
        }

    if archetype == "experiencia":
        return {
            "start_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=64)).isoformat(),
            "timezone": "America/Mexico_City",
            "location_type": "DESTINATION_RETREAT",
            "venue_name": "Hotel Xcaret Arte",
            "accommodation_type": "LUXURY_SUITE",
            "agenda_highlights": ["Cena de Bienvenida", "Mastermind Session", "Yoga al amanecer"],
            "is_transfer_included": True,
        }

    return {}


def seed_offers():
    session = SessionLocal()
    try:
        products = session.query(Product).all()
        print(f"Found {len(products)} products to seed.")

        updated_count = 0
        for product in products:
            if not product.archetype:
                print(f"Skipping product {product.id} (No Archetype)")
                continue

            details = get_dummy_details(product.archetype)

            if not product.specific_details:
                product.specific_details = details
                updated_count += 1
                print(f"Updated {product.name} ({product.archetype})")

        session.commit()
        print(f"\nSeeded {updated_count} products with specific_details.")
    finally:
        session.close()


if __name__ == "__main__":
    seed_offers()
