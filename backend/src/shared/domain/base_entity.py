"""Base entities for SQLAlchemy and Pydantic domain models."""

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseEntity(BaseModel):
    """Base Pydantic model for domain entities with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
