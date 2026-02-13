import sys
import os
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Add backend directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.db.models.business import Product
from src.core.domain.offer_enums import (
    OfferType, OfferDeliveryModel, OfferValueLevel, FulfillmentType, DigitalFormat,
    ProgramStructure, LiveInteractionType, CommunityPlatform, ServiceCategory,
    InteractionMode, ServiceFrequency, EventLocationType, AccommodationType,
    BillingFrequency
)

# Database Connection (Adjust URL if needed, assuming default dev container)
DATABASE_URL = "postgresql://postgres:password@localhost:5432/visionarias_logs" 
# NOTE: In production or docker, this might differ. Assuming running from 'backend/' or root context.

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_dummy_details(offer_type: str):
    """Generates dummy specific_details based on OfferType."""
    
    # --- LEVEL 0 & 1: PRODUCTS (DIY) ---
    if offer_type in [OfferType.FREE_RESOURCE, OfferType.TRIPWIRE_OFFER, OfferType.SELF_PACED_COURSE, OfferType.PHYSICAL_MERCH, OfferType.CONTENT_ASSET_PODCAST]:
        is_physical = offer_type == OfferType.PHYSICAL_MERCH
        return {
            "fulfillment_type": "PHYSICAL_SHIPPING" if is_physical else "DIRECT_DOWNLOAD",
            "access_url": "https://example.com/download" if not is_physical else None,
            "format": "PHYSICAL" if is_physical else "PDF",
            "is_downloadable": True,
            "requires_shipping": is_physical,
            "sku_inventory_code": "SKU-123" if is_physical else None,
            "stock_quantity": 100 if is_physical else None
        }

    # --- LEVEL 2: PROGRAMS (DWY - Cohorts/Mentorships) ---
    if offer_type in [OfferType.HYBRID_MENTORSHIP, OfferType.COHORT_BASED_COURSE, OfferType.GROUP_COACHING_PROGRAM, OfferType.FREE_WEBINAR_CHALLENGE]:
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
            "community_invite_link": "https://skool.com/community"
        }

    # --- LEVEL 3 & 4: SERVICES (Advisory/Agency) ---
    if offer_type in [OfferType.VIP_DAY_STRATEGY, OfferType.ONE_ON_ONE_PRIVATE_MENTORING, OfferType.DEEP_DIVE_AUDIT, 
                      OfferType.PRODUCTIZED_SERVICE, OfferType.CORPORATE_TRAINING, OfferType.KEYNOTE_SPEAKING, OfferType.BRAND_SPONSORSHIP]:
        is_agency = offer_type in [OfferType.PRODUCTIZED_SERVICE, OfferType.BRAND_SPONSORSHIP]
        return {
            "category": "EXECUTION_AGENCY" if is_agency else "ADVISORY",
            "interaction_mode": "ASYNC_DELIVERY" if is_agency else "SYNC_LIVE",
            "frequency_type": "ONE_OFF",
            "deliverables_list": ["Auditoría PDF", "Plan de Acción", "Grabación de Sesión"],
            "booking_url": "https://calendly.com/expert/vip-day" if not is_agency else None,
            "turnaround_time_days": 7 if is_agency else None,
            "technical_requirements": "Logo vectorizado y Brand Book" if offer_type == OfferType.BRAND_SPONSORSHIP else None
        }

    # --- LEVEL 4 & 5: RETAINERS & SUBSCRIPTIONS ---
    if offer_type in [OfferType.MONTHLY_RETAINER, OfferType.PAID_NEWSLETTER_SUBSCRIPTION, OfferType.COMMUNITY_LITE, OfferType.PERFORMANCE_REV_SHARE]:
        # Note: Retainers map to ServiceDetails, but Subscriptions map to SubscriptionDetails.
        # Checking schema mapping logic:
        if offer_type in [OfferType.MONTHLY_RETAINER, OfferType.PERFORMANCE_REV_SHARE]:
            # ServiceDetails
            return {
                "category": "EXECUTION_AGENCY",
                "interaction_mode": "ASYNC_DELIVERY",
                "frequency_type": "RETAINER",
                "min_contract_months": 3,
                "deliverables_list": ["4 Videos/mes", "Gestión de Ads"],
                "onboarding_brief_url": "https://tally.so/r/brief"
            }
        else:
            # SubscriptionDetails
            return {
                "billing_cycle": "MONTHLY",
                "tier_name": "Pro Member",
                "platform_name": "Skool",
                "cancellation_policy": "Cancel anytime",
                "content_update_freq": "Weekly"
            }

    # --- LEVEL 5: EVENTS ---
    if offer_type in [OfferType.LUXURY_RETREAT, OfferType.MASTERMIND_NETWORK]:
        return {
            "start_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=64)).isoformat(),
            "timezone": "America/Mexico_City",
            "location_type": "DESTINATION_RETREAT",
            "venue_name": "Hotel Xcaret Arte",
            "accommodation_type": "LUXURY_SUITE",
            "agenda_highlights": ["Cena de Bienvenida", "Mastermind Session", "Yoga al amanecer"],
            "is_transfer_included": True
        }

    return {}

def seed_offers():
    session = SessionLocal()
    try:
        products = session.query(Product).all()
        print(f"Found {len(products)} products to seed.")
        
        updated_count = 0
        for product in products:
            if not product.type:
                print(f"Skipping product {product.id} (No Type)")
                continue
                
            # Generate dummy details
            details = get_dummy_details(product.type)
            
            # Update specific_details
            # We use dict update to preserve existing keys if any (optional)
            # checking if it's empty to overwrite
            if not product.specific_details:
                product.specific_details = details
                updated_count += 1
                print(f"Updated {product.name} ({product.type})")
        
        session.commit()
        print(f"Successfully seeded {updated_count} offers with dummy details.")
        
    except Exception as e:
        print(f"Error seeding offers: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_offers()
