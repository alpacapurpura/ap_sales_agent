# Re-exports from core database for backwards compatibility within sales_agent module
from src.core.database import engine as engine
from src.core.database import SessionLocal as SessionLocal
from src.core.database import redis_client as redis_client
from src.core.database import get_db as get_db
from src.core.database import init_db as init_db
