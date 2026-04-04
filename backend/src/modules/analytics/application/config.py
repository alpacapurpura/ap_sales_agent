"""Analytics module configuration constants.

Centralizes magic numbers previously scattered across services, workers, and API routes.
"""


class ETLConfig:
    """ETL pipeline configuration."""

    MAX_LOOKBACK_DAYS: int = 60
    EXTRACTION_TIMEOUT_SECONDS: int = 600
    MAX_CONCURRENT_JOBS: int = 10
    MAX_RETRIES: int = 5
    GLOBAL_SYNC_COOLDOWN: int = 120  # seconds
    PER_PROVIDER_REFRESH_COOLDOWN: int = 900  # 15 min
    PER_CHANNEL_REFRESH_COOLDOWN: int = 60
    IG_INSIGHTS_MAX_CHUNK_DAYS: int = 30
    DAILY_EXTRACTION_HOUR_LOCAL: int = 3


class CacheConfig:
    """Redis cache TTLs (seconds)."""

    ATTRACTION_TTL: int = 3600  # 1 hour
    DETAIL_STAGE_TTL: int = 300  # 5 minutes
    SUMMARY_TTL: int = 60  # 1 minute
    CATALOG_TTL: int = 3600  # 1 hour
    DEFAULT_TTL: int = 300  # 5 minutes
