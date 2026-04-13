"""Database infrastructure module."""

# Re-exports from core database for backwards compatibility within sales_agent module
from src.core.database import SessionLocal  # noqa: F401
