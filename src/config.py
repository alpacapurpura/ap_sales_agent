from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visionarias Brain"
    
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
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"
    
    # Provider Selection
    AI_PROVIDER: str = "openai" # openai, gemini, etc.
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str = "" # Optional if running locally without auth, but required for prod
    QDRANT_COLLECTION: str = "visionarias_knowledge"
    
    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"

settings = Settings()
