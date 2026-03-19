from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
import redis

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_db():
    """Dependency for FastAPI routers to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(base_metadata=None):
    """Initialize database tables."""
    if base_metadata:
        base_metadata.create_all(bind=engine)

