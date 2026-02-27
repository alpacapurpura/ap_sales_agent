import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import logging

# Add backend to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.shared.infrastructure.db.database import engine
from src.modules.marketing.infrastructure.models.customer_model import CustomerProfileModel as CustomerProfile, CustomerIdentityModel as CustomerIdentity
from src.modules.marketing.domain.enums import IdentityType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Add customer_id column if not exists
        logger.info("Checking/Adding customer_id column...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customer_profiles(id)"))
            conn.commit()

        # 2. Migrate Data
        logger.info("Migrating data...")
        
        # Fetch all leads using raw SQL to access deleted columns
        # Note: We select columns that might have been removed from the ORM model but still exist in DB
        result = session.execute(text("SELECT id, full_name, email, phone, social_handle_main, timezone, tenant_id FROM leads"))
        leads_data = result.fetchall()

        for row in leads_data:
            lead_id = row.id
            full_name = row.full_name
            email = row.email
            phone = row.phone
            social_handle = row.social_handle_main
            timezone = row.timezone
            tenant_id = row.tenant_id

            if not email and not phone:
                logger.warning(f"Lead {lead_id} has no email or phone. Skipping profile creation.")
                continue

            # Find existing profile
            profile = None
            if email:
                profile = session.query(CustomerProfile).filter(CustomerProfile.primary_email == email).first()
            if not profile and phone:
                profile = session.query(CustomerProfile).filter(CustomerProfile.primary_phone == phone).first()

            if not profile:
                # Create new profile
                logger.info(f"Creating profile for Lead {lead_id} ({email or phone})")
                profile = CustomerProfile(
                    full_name=full_name,
                    primary_email=email,
                    primary_phone=phone,
                    tenant_id=tenant_id,
                    traits={
                        "social_handle_main": social_handle,
                        "timezone": timezone,
                        "source": "lead_migration"
                    }
                )
                session.add(profile)
                session.flush() # Get ID
                
                # Add Identity
                if email:
                    session.add(CustomerIdentity(profile_id=profile.id, type=IdentityType.EMAIL, value=email, is_primary=True))
                if phone:
                    session.add(CustomerIdentity(profile_id=profile.id, type=IdentityType.PHONE, value=phone, is_primary=False))

            # Update Lead
            session.execute(
                text("UPDATE leads SET customer_id = :cid WHERE id = :lid"),
                {"cid": profile.id, "lid": lead_id}
            )
        
        session.commit()
        logger.info("Data migration completed.")

        # 3. Drop old columns
        logger.info("Dropping old columns...")
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE leads DROP COLUMN IF EXISTS full_name"))
            except Exception as e:
                logger.warning(f"Error dropping full_name: {e}")
            
            try:
                conn.execute(text("ALTER TABLE leads DROP COLUMN IF EXISTS email"))
            except Exception as e:
                logger.warning(f"Error dropping email: {e}")

            try:
                conn.execute(text("ALTER TABLE leads DROP COLUMN IF EXISTS phone"))
            except Exception as e:
                logger.warning(f"Error dropping phone: {e}")

            try:
                conn.execute(text("ALTER TABLE leads DROP COLUMN IF EXISTS social_handle_main"))
            except Exception as e:
                logger.warning(f"Error dropping social_handle_main: {e}")

            try:
                conn.execute(text("ALTER TABLE leads DROP COLUMN IF EXISTS timezone"))
            except Exception as e:
                logger.warning(f"Error dropping timezone: {e}")
            
            conn.commit()
        
        logger.info("Migration finished successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
