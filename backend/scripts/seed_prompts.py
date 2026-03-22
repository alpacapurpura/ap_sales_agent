import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.services.database import SessionLocal
from src.services.db.models import PromptVersion
from sqlalchemy import select

# 1. Definir los prompts iniciales y sus metadatos manuales
# (Ya que inferir todo es difícil, mejor mapeamos la inteligencia aquí)
INITIAL_PROMPTS = [
    {
        "key": "sales_system",
        "file": "src/core/prompts/templates/sales_system.j2",
        "change_reason": "Migración inicial (Seed)",
        "metadata_info": {
            "target_node": "response_generation",
            "target_model": "gpt-4-turbo",
            "input_variables": ["current_state", "user_profile", "active_strategy", "context_rag"],
            "description": "Prompt principal del sistema que define la personalidad y lógica de respuesta del agente."
        }
    },
    {
        "key": "state_transition",
        "file": "src/core/prompts/templates/state_transition.j2",
        "change_reason": "Migración inicial (Seed)",
        "metadata_info": {
            "target_node": "manager",
            "target_model": "gpt-3.5-turbo", # O smart model
            "input_variables": ["current_state", "user_profile", "last_user_message"],
            "description": "Cerebro cognitivo que decide el siguiente paso y extrae información del usuario."
        }
    },
    {
        "key": "summary_generator",
        "file": "src/core/prompts/templates/summary_generator.j2",
        "change_reason": "Migración inicial (Seed)",
        "metadata_info": {
            "target_node": "manager",
            "target_model": "gpt-3.5-turbo",
            "input_variables": ["messages", "user_profile"],
            "description": "Genera resúmenes de memoria episódica."
        }
    },
     {
        "key": "hyde_generator",
        "file": "src/core/prompts/templates/hyde_generator.j2",
        "change_reason": "Migración inicial (Seed)",
        "metadata_info": {
            "target_node": "rag_query_expander",
            "target_model": "gpt-3.5-turbo",
            "input_variables": ["query"],
            "description": "Hypothetical Document Embeddings - Genera documentos falsos para mejorar la búsqueda."
        }
    }
]

def seed_prompts():
    db = SessionLocal()
    print("🌱 Iniciando siembra de Prompts...")
    
    try:
        for p_config in INITIAL_PROMPTS:
            key = p_config["key"]
            file_path = p_config["file"]
            
            if not os.path.exists(file_path):
                print(f"⚠️ Archivo no encontrado: {file_path}, saltando.")
                continue
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Verificar si ya existe alguna versión
            existing = db.execute(
                select(PromptVersion).where(PromptVersion.key == key)
            ).scalars().first()
            
            if existing:
                print(f"ℹ️ El prompt '{key}' ya existe en BD. Saltando.")
                continue
            
            # Crear Versión 1
            prompt_v1 = PromptVersion(
                key=key,
                version=1,
                content=content,
                is_active=True,
                change_reason=p_config["change_reason"],
                author_id="system_seed",
                metadata_info=p_config["metadata_info"]
            )
            
            db.add(prompt_v1)
            print(f"✅ Creado prompt '{key}' (v1).")
        
        db.commit()
        print("🌱 Siembra completada exitosamente.")
        
    except Exception as e:
        print(f"❌ Error durante el seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_prompts()
