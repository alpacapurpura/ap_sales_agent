import sys
import os
import time

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from sqlalchemy import text
from src.services.database import engine, SessionLocal
from src.services.db.models.user import User
from src.services.db.models.lead import Lead

def migrate():
    print("Starting migration: Split 'users' into 'leads' and 'users'...")
    
    # Step 1: DDL Operations (Rename Table)
    # Use engine.begin() for transaction management (auto-commit on success)
    with engine.begin() as conn:
        # Check existence
        leads_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'leads')")).scalar()
        
        if leads_exists:
            count = conn.execute(text("SELECT count(*) FROM leads")).scalar()
            if count == 0:
                print("⚠️ Table 'leads' exists but is empty. Dropping it to allow rename.")
                conn.execute(text("DROP TABLE leads CASCADE"))
                leads_exists = False
            else:
                print(f"ℹ️ Table 'leads' exists and has {count} rows. Skipping rename.")

        if not leads_exists:
            print("Renaming 'users' to 'leads'...")
            try:
                conn.execute(text("ALTER TABLE users RENAME TO leads"))
                print("✅ Table renamed.")
            except Exception as e:
                print(f"❌ Rename failed: {e}")
                # We raise here to rollback transaction if rename fails
                raise e

    # Step 2: Create new 'users' table
    print("Creating new 'users' table...")
    try:
        # Create table using the schema defined in User model
        # User maps to 'users' table
        User.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table 'users' created (or already exists).")
    except Exception as e:
        print(f"❌ Create table failed: {e}")
        return

    # Step 3: Migrate Admin Data
    session = SessionLocal()
    try:
        print("Migrating potential admins from 'leads' to 'users'...")
        # Fetch all leads that have an email (potential system users)
        leads_with_email = session.query(Lead).filter(Lead.email.isnot(None)).all()
        
        migrated_count = 0
        for lead in leads_with_email:
            exists = session.query(User).filter(User.email == lead.email).first()
            
            if not exists:
                new_user = User(
                    id=lead.id, 
                    full_name=lead.full_name,
                    email=lead.email,
                    phone=lead.phone,
                    tenant_id=lead.tenant_id,
                    role="admin", 
                    is_active=True
                )
                session.add(new_user)
                migrated_count += 1
                print(f"   -> Migrating: {lead.email} ({lead.full_name})")
        
        session.commit()
        print(f"✅ Migration complete. {migrated_count} users copied to System Users table.")
        
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
