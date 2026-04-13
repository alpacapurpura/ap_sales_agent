"""CRM infrastructure models package."""

from src.modules.crm.infrastructure.models.customer_model import (
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
)
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)

__all__ = [
    "CustomerIdentityModel",
    "CustomerProfileModel",
    "JourneyEventModel",
    "LifecycleTransitionModel",
]
