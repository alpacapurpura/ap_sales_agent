import sys
import os
from sqlalchemy import text, inspect

# Add backend to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.services.database import engine, Base

def sync_schema():
    print("🔄 Starting Schema Synchronization...")
    inspector = inspect(engine)
    
    # 1. Create tables if they don't exist
    # This covers 'avatar_definitions' if it's missing entirely
    print("Checking for new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ create_all executed (created missing tables)")

    # 2. Check for missing columns in 'products'
    # Specifically 'avatar_id'
    print("Checking 'products' table schema...")
    columns = [c['name'] for c in inspector.get_columns('products')]
    
    with engine.connect() as conn:
        if 'avatar_id' not in columns:
            print("⚠️ 'avatar_id' column missing in 'products'. Adding it...")
            try:
                conn.execute(text("ALTER TABLE products ADD COLUMN avatar_id UUID REFERENCES avatar_definitions(id)"))
                conn.commit()
                print("✅ 'avatar_id' column added.")
            except Exception as e:
                print(f"❌ Error adding column: {e}")
        else:
            print("✅ 'avatar_id' exists in 'products'.")

    # 3. Check for missing columns in 'avatar_definitions'
    # Just in case the table existed but was old
    print("Checking 'avatar_definitions' table schema...")
    # Refresh inspector just in case table was created in step 1
    inspector = inspect(engine)
    avatar_cols = [c['name'] for c in inspector.get_columns('avatar_definitions')]
    
    expected_cols = ['scope', 'icp_description', 'anti_avatar', 'voice_tone_config', 'is_default']
    
    with engine.connect() as conn:
        for col in expected_cols:
            if col not in avatar_cols:
                print(f"⚠️ '{col}' column missing in 'avatar_definitions'. Adding it...")
                try:
                    # Determine type
                    col_type = "TEXT"
                    if col == "voice_tone_config":
                        col_type = "JSONB DEFAULT '{}'"
                    elif col == "is_default":
                        col_type = "BOOLEAN DEFAULT FALSE"
                    elif col == "scope":
                        col_type = "VARCHAR DEFAULT 'GLOBAL'"
                        
                    conn.execute(text(f"ALTER TABLE avatar_definitions ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    print(f"✅ '{col}' column added.")
                except Exception as e:
                    print(f"❌ Error adding column '{col}': {e}")
            else:
                print(f"✅ '{col}' exists.")

    print("🏁 Schema Synchronization Completed.")

if __name__ == "__main__":
    sync_schema()
