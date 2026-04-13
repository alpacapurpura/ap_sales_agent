from __future__ import annotations

from typing import TYPE_CHECKING

import redis
import structlog
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Generator

logger = structlog.get_logger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis — graceful degradation when unavailable
_redis_client: redis.Redis | None = None
try:
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_client.ping()
    logger.info("redis_connected", url=settings.REDIS_URL)
except (redis.ConnectionError, redis.TimeoutError, OSError) as exc:
    logger.warning(
        "redis_unavailable",
        url=settings.REDIS_URL,
        error=str(exc),
        hint="App will start without Redis; cache/queue features degraded",
    )
    _redis_client = None

redis_client: redis.Redis | None = _redis_client


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routers to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(base_metadata: MetaData | None = None) -> None:
    """Initialize database tables."""
    if base_metadata:
        base_metadata.create_all(bind=engine)
