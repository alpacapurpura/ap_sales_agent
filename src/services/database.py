import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from src.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Redis Client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Postgres Connection (SQLAlchemy for ORM if needed, but simple psycopg2 for logging is fine too)
# We'll use SQLAlchemy for better management
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
