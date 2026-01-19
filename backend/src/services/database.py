import redis
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings
from src.services.db.models._base import Base
from src.services.db.models.business import Product, PromptVersion
import os

# Redis Client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Postgres Connection
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize DB tables and seed initial data.
    """
    # Create tables (SAFE: Only creates if not exists)
    # Base.metadata.drop_all(bind=engine) # DISABLED: Prevent data loss on restart
    Base.metadata.create_all(bind=engine)
    
    # Seed Data (Check existence first to avoid duplicates)
    db = SessionLocal()
    try:
        # Check if products already exist
        if db.query(Product).first():
            print("✨ Database already initialized. Skipping seed.")
            return

        # --- 1. Products ---
        ht_name = "Programa de propósito a progreso"
        ht_product = Product(
            name=ht_name,
            type="program",
            # tier="high_ticket", # Removed as not in model
            status="active",
            pricing={
                "regular": 5925, 
                "offer": 4444, 
                "currency": "PEN"
            },
            dates={
                "start": "2026-02-10", 
                "offer_deadline": "2026-02-08"
            },
            metadata_info={
                "description": "Programa Intensivo de Emprendimiento Femenino de 8 semanas.",
                "guarantee": "Devolución completa en la primera semana."
            }
        )
        db.add(ht_product)

        # 2. Lead Magnet (Webinar)
        lm_name = "Webinar para mujeres que quieren emprender"
        lm_product = Product(
            name=lm_name,
            type="webinar",
            # tier="lead_magnet", # Removed as not in model
            status="active",
            pricing={"regular": 0, "currency": "PEN"},
            dates={"start": "2026-01-20"}, # Simulado
            metadata_info={
                "description": "Webinar gratuito de captación.",
                "funnel_role": "awareness_builder"
            }
        )
        db.add(lm_product)
        
        # --- 2. Prompts (Seed) ---
        print("🌱 Seeding initial prompts...")
        INITIAL_PROMPTS = [
            {
                "key": "sales_system",
                "file": "src/core/prompts/templates/sales_system.j2",
                "change_reason": "System Initialization",
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
                "change_reason": "System Initialization",
                "metadata_info": {
                    "target_node": "manager",
                    "target_model": "gpt-3.5-turbo",
                    "input_variables": ["current_state", "user_profile", "last_user_message"],
                    "description": "Cerebro cognitivo que decide el siguiente paso y extrae información del usuario."
                }
            },
            {
                "key": "summary_generator",
                "file": "src/core/prompts/templates/summary_generator.j2",
                "change_reason": "System Initialization",
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
                "change_reason": "System Initialization",
                "metadata_info": {
                    "target_node": "manager",
                    "target_model": "gpt-3.5-turbo",
                    "input_variables": ["query"],
                    "description": "Hypothetical Document Embeddings - Genera documentos falsos para mejorar la búsqueda."
                }
            }
        ]
        
        base_path = os.getcwd()
        for p_config in INITIAL_PROMPTS:
            # Try to find file, relative to CWD or absolute
            file_path = p_config["file"]
            if not os.path.exists(file_path):
                 # Try absolute if CWD is not root
                 file_path = os.path.join(base_path, p_config["file"])
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                prompt = PromptVersion(
                    key=p_config["key"],
                    version=1,
                    content=content,
                    is_active=True,
                    change_reason=p_config["change_reason"],
                    author_id="system",
                    metadata_info=p_config["metadata_info"]
                )
                db.add(prompt)
                print(f"   + Prompt: {p_config['key']}")
            else:
                print(f"   ⚠️ Prompt file not found: {file_path}")

        db.commit()
        print(f"Seeded products and prompts successfully.")
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
