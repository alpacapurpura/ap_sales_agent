import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path to allow imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.config import settings
from src.services.db.models.tenant import Tenant

def init_tenant_data():
    print("Starting Tenant Data Backfill...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    # 1. Check/Create "Visionarias" Tenant
    visionarias = session.query(Tenant).filter(Tenant.slug == "visionarias").first()
    
    if not visionarias:
        print("Creating default tenant 'Visionarias'...")
        config = {
            "company_name": "Visionarias",
            "bot_name": "Visionaria",
            "price_regular": "S/. 740",
            "price_offer": "S/. 444",
            "authorities": "Camila e Ileana"
        }
        visionarias = Tenant(
            name="Visionarias",
            slug="visionarias",
            config_json=config,
            is_active=True
        )
        session.add(visionarias)
        session.commit()
        session.refresh(visionarias)
        print(f"✅ Created Tenant: {visionarias.id}")
    else:
        print(f"ℹ️ Tenant 'Visionarias' already exists ({visionarias.id})")

    tenant_id = visionarias.id
    
    # 2. Assign Tenant ID to all existing tables (Backfill)
    tables_to_update = [
        "users", "products", "enrollments", "messages", 
        "agent_traces", "llm_call_logs", "marketing_assets",
        "documents", "objections", "offer_logs", 
        "prompt_versions", "sensitive_data", "avatar_definitions"
    ]
    
    for table in tables_to_update:
        print(f"Updating {table}...")
        try:
            # Raw SQL for speed and simplicity
            stmt = text(f"UPDATE {table} SET tenant_id = :tid WHERE tenant_id IS NULL")
            result = session.execute(stmt, {"tid": tenant_id})
            print(f"  -> Updated {result.rowcount} rows in {table}")
        except Exception as e:
            print(f"  ❌ Error updating {table}: {e}")
            
    try:
        session.commit()
        print("✅ Data Backfill Completed Successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error committing backfill: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    init_tenant_data()
