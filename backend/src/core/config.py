"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings

from src.core.enums import AIProvider, ModelRole, PromptSource


class Settings(BaseSettings):
    """Environment-driven application settings."""

    # API Config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visionarias Brain"
    LOG_LEVEL: str  # Defined in .env
    DOMAIN_NAME: str  # Defined in .env
    TRAEFIK_NETWORK: str  # Defined in .env

    # Security
    API_SECRET_KEY: str  # Must be set in environment!

    # WhatsApp / Meta
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_VERIFY_TOKEN: str

    # Evolution API (Self-Hosted)
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_VERSION: str = "v1"  # Options: "v1", "v2"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""  # Set in .env per environment

    # -- Meta (Facebook/Instagram) --
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""
    META_REDIRECT_URI: str = ""  # Set in .env per environment
    META_CONFIG_ID: str = ""  # Facebook Login for Business configuration ID

    # Shopify
    SHOPIFY_API_KEY: str = ""
    SHOPIFY_API_SECRET: str = ""
    SHOPIFY_APP_URL: str = ""  # The URL where the app is hosted (e.g. https://api.visionarias.ai)

    # OpenAI
    OPENAI_API_KEY: str

    # DeepSeek (OpenAI-compatible API)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Kimi / Moonshot (OpenAI-compatible API)
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"

    # Qwen / Alibaba DashScope (OpenAI-compatible intl endpoint)
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # --- AI Model Registry ---
    # Each role maps to a concrete model. Override per-role via env vars.
    # NANO defaults to gpt-4o-mini until OpenAI catalog exposes a smaller tier
    # in our deployed envs (override via AI_MODEL_NANO env var).
    AI_MODEL_NANO: str = "gpt-4o-mini"
    AI_MODEL_REASONING: str = "gpt-4o"
    AI_MODEL_FAST: str = "gpt-4o-mini"
    AI_MODEL_VISION: str = "gpt-4o"
    AI_MODEL_AGENT: str = "gpt-4o"
    AI_MODEL_EMBEDDING: str = "text-embedding-3-large"

    def get_model(self, role: ModelRole) -> str:
        """Resolve a semantic role to a concrete model name."""
        _map = {
            ModelRole.NANO: self.AI_MODEL_NANO,
            ModelRole.REASONING: self.AI_MODEL_REASONING,
            ModelRole.FAST: self.AI_MODEL_FAST,
            ModelRole.VISION: self.AI_MODEL_VISION,
            ModelRole.AGENT: self.AI_MODEL_AGENT,
            ModelRole.EMBEDDING: self.AI_MODEL_EMBEDDING,
        }
        return _map[role]

    def get_provider_for_role(self, role: ModelRole) -> AIProvider:
        """Resolve which provider serves a given role.

        Per-role override (``AI_PROVIDER_<ROLE>``) wins; falls back to global
        ``AI_PROVIDER``. Lets us run e.g. NANO/FAST on OpenAI for low TTFB
        while REASONING/AGENT/HEAVY route to DeepSeek/Kimi for cost.
        """
        _overrides = {
            ModelRole.NANO: self.AI_PROVIDER_NANO,
            ModelRole.REASONING: self.AI_PROVIDER_REASONING,
            ModelRole.FAST: self.AI_PROVIDER_FAST,
            ModelRole.VISION: self.AI_PROVIDER_VISION,
            ModelRole.AGENT: self.AI_PROVIDER_AGENT,
            ModelRole.EMBEDDING: self.AI_PROVIDER_EMBEDDING,
        }
        return _overrides.get(role) or self.AI_PROVIDER

    @property
    def openai_model(self) -> str:
        """Return the default reasoning model name."""
        return self.AI_MODEL_REASONING

    @property
    def openai_fast_model(self) -> str:
        """Return the fast model name."""
        return self.AI_MODEL_FAST

    @property
    def openai_embedding_model(self) -> str:
        """Return the embedding model name."""
        return self.AI_MODEL_EMBEDDING

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"

    # Provider Selection — global default, overridable per-role below.
    AI_PROVIDER: AIProvider = AIProvider.OPENAI  # openai/gemini/deepseek/kimi/qwen

    # Per-role provider override (optional). Empty/unset → fall back to AI_PROVIDER.
    AI_PROVIDER_NANO: AIProvider | None = None
    AI_PROVIDER_REASONING: AIProvider | None = None
    AI_PROVIDER_FAST: AIProvider | None = None
    AI_PROVIDER_VISION: AIProvider | None = None
    AI_PROVIDER_AGENT: AIProvider | None = None
    AI_PROVIDER_EMBEDDING: AIProvider | None = None
    PROMPT_SOURCE: PromptSource = PromptSource.HYBRID  # hybrid, file, db

    # Brand Extraction Profile: "safe" (2-wave, low rate-limit) or "fast" (all-concurrent, high rate-limit)
    BRAND_EXTRACTION_PROFILE: str = "safe"

    # Redis
    REDIS_URL: str  # Must be set in .env (e.g. redis://redis:6379/0)

    # Qdrant
    QDRANT_URL: str  # Must be set in .env (e.g. http://qdrant:6333)
    QDRANT_API_KEY: str = ""  # Optional if running locally without auth, but required for prod
    QDRANT_COLLECTION: str = "visionarias_knowledge"
    QDRANT_COLLECTION_HYBRID: str = "visionarias_hybrid"
    QDRANT_VECTOR_SIZE: int = 3072  # Default for text-embedding-3-large
    QDRANT_SPARSE_MODEL: str = "Qdrant/bm25"  # or "prithivida/Splade_PP_en_v1"

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

    # Cloudflare Domains (Custom Domains feature)
    CLOUDFLARE_ZONE_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_KV_NAMESPACE_ID: str = ""

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

    # Tavily (web search for AI agents)
    TAVILY_API_KEY: str = ""

    # Sentry / Environment
    SENTRY_DSN: str = ""
    SENTRY_WORKER_DSN: str = ""  # Workers project DSN — falls back to SENTRY_DSN if empty
    ENVIRONMENT: str = "dev"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1
    SENTRY_RELEASE: str = "dev"

    # CORS
    CORS_ORIGINS: list[str] = []

    @property
    def database_url(self) -> str:
        """Build the PostgreSQL connection URL from component settings."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        extra = "ignore"


settings = Settings()
