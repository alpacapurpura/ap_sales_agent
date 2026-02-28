from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings
import redis
from src.shared.infrastructure.db.base_model import Base

# Create engine
engine = create_engine(settings.DATABASE_URL)

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

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
