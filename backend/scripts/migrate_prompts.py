import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path to allow imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.core.config import settings
from src.services.db.models.business import PromptVersion

# Replacements Map for Visionarias -> Generic
REPLACEMENTS = {
    "Visionarias": "{{ company_name }}",
    "Visionaria": "{{ bot_name }}",
    "Camilia e Ileana": "{{ authorities }}",
    "Camilia": "{{ authorities }}", # Safety catch if separated
    "S/. 740.67": "{{ price_regular }}",
    "S/. 4,444": "{{ price_offer }}"
}

def migrate():
    print("Starting Prompt Migration to DB...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return

    # Read Files
    prompts_dir = "backend/src/core/prompts/templates"
    if not os.path.exists(prompts_dir):
        print(f"Directory not found: {prompts_dir}")
        return

    for filename in os.listdir(prompts_dir):
        if filename.endswith(".j2"):
            file_path = os.path.join(prompts_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Apply replacements to make it generic
            # Note: This is a simple replace. Manual review might be needed.
            processed_content = content
            for old, new in REPLACEMENTS.items():
                processed_content = processed_content.replace(old, new)
                
            key = filename.replace(".j2", "")
            
            # Check if exists (System Default -> tenant_id=None)
            existing = session.query(PromptVersion).filter(
                PromptVersion.key == key, 
                PromptVersion.tenant_id == None,
                PromptVersion.version == 1
            ).first()
            
            if not existing:
                pv = PromptVersion(
                    key=key,
                    version=1,
                    content=processed_content,
                    is_active=True,
                    change_reason="Initial Migration: File to DB",
                    tenant_id=None,
                    metadata_info={"original_file": filename}
                )
                session.add(pv)
                print(f"✅ Migrated: {key} (Genericized)")
            else:
                print(f"⏩ Skipped: {key} (Already exists)")
                
    try:
        session.commit()
        print("Migration Commit Successful.")
    except Exception as e:
        session.rollback()
        print(f"Error committing: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
