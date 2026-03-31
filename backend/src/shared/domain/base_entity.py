from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict

Base = declarative_base()

class BaseEntity(BaseModel):
    """
    Base Pydantic model for domain entities.
    Enables ORM mode by default.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
