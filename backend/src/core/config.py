from pydantic_settings import BaseSettings
from src.core.enums import PromptSource, AIProvider

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
    
    # Evolution API (Self-Hosted)
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_VERSION: str = "v1" # Options: "v1", "v2"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""  # Set in .env per environment

    # Meta (Facebook/Instagram)
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""
    META_REDIRECT_URI: str = ""  # Set in .env per environment
    META_CONFIG_ID: str = ""  # Facebook Login for Business configuration ID

    # Shopify
    SHOPIFY_API_KEY: str = ""
    SHOPIFY_API_SECRET: str = ""
    SHOPIFY_APP_URL: str = "" # The URL where the app is hosted (e.g. https://api.visionarias.ai)
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview" # Reasoning Model (Slow/Smart)
    OPENAI_FAST_MODEL: str = "gpt-3.5-turbo" # Response Model (Fast/Cheap)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"
    
    # Provider Selection
    AI_PROVIDER: AIProvider = AIProvider.OPENAI # openai, gemini, etc.
    PROMPT_SOURCE: PromptSource = PromptSource.HYBRID # hybrid, file, db
    
    # Redis
    REDIS_URL: str  # Must be set in .env (e.g. redis://redis:6379/0)

    # Qdrant
    QDRANT_URL: str  # Must be set in .env (e.g. http://qdrant:6333)
    QDRANT_API_KEY: str = "" # Optional if running locally without auth, but required for prod
    QDRANT_COLLECTION: str = "visionarias_knowledge"
    QDRANT_COLLECTION_HYBRID: str = "visionarias_hybrid"
    QDRANT_VECTOR_SIZE: int = 3072 # Default for text-embedding-3-large
    QDRANT_SPARSE_MODEL: str = "Qdrant/bm25" # or "prithivida/Splade_PP_en_v1"
    
    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str  # Must be set in .env (e.g. postgres)
    POSTGRES_PORT: int  # Must be set in .env (e.g. 5432)

    # Production Domains
    API_DOMAIN: str = ""
    DASHBOARD_DOMAIN: str = ""
    API_URL: str  # Internal URL for webhooks — set in .env per environment
    UPLOAD_DIR: str = "static/uploads"

    # Storage Provider: "LOCAL" or "R2"
    STORAGE_PROVIDER: str = "LOCAL"

    # Cloudflare R2
    CLOUDFLARE_ACCOUNT_ID: str = ""
    R2_BUCKET_NAME: str = ""
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_PUBLIC_URL: str = ""  # Public base URL, e.g. https://assets-dev.nicolify.com
    
    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""

    # Sentry / Environment
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "dev"

    # CORS
    CORS_ORIGINS: list[str] = []

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
