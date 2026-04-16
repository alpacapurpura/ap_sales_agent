"""CRM customer SQLAlchemy models — re-exported from shared for backward compatibility."""

# These models now live in src.shared.infrastructure.models.crm so that
# analytics, sales_agent, and other modules can import them without
# violating DDD boundaries.  CRM-internal code still uses this path.
from src.shared.infrastructure.models.crm import (
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
)

__all__ = [
    "CustomerIdentityModel",
    "CustomerProfileModel",
    "JourneyEventModel",
]
