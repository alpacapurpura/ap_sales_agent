from pydantic_settings import BaseSettings
from src.core.schema import PromptSource

class Settings(BaseSettings):
    # API Config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visionarias Brain"
    LOG_LEVEL: str # Defined in .env
    DOMAIN_NAME: str # Defined in .env
    TRAEFIK_NETWORK: str # Defined in .env
    
    # Security
    API_SECRET_KEY: str # Must be set in environment!
    
    # WhatsApp / Meta
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_VERIFY_TOKEN: str
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview" # Reasoning Model (Slow/Smart)
    OPENAI_FAST_MODEL: str = "gpt-3.5-turbo" # Response Model (Fast/Cheap)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"
    
    # Provider Selection
    AI_PROVIDER: str = "openai" # openai, gemini, etc.
    PROMPT_SOURCE: PromptSource = PromptSource.HYBRID # hybrid, file, db
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str = "" # Optional if running locally without auth, but required for prod
    QDRANT_COLLECTION: str = "visionarias_knowledge"
    QDRANT_COLLECTION_HYBRID: str = "visionarias_hybrid"
    QDRANT_VECTOR_SIZE: int = 3072 # Default for text-embedding-3-large
    QDRANT_SPARSE_MODEL: str = "Qdrant/bm25" # or "prithivida/Splade_PP_en_v1"
    
    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"

settings = Settings()
