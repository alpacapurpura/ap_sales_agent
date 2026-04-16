"""NPS survey and response models — re-exported from shared for backward compatibility."""

# These models now live in src.shared.infrastructure.models.crm so that
# analytics can import them without violating DDD boundaries.
from src.shared.infrastructure.models.crm import NpsResponseModel, NpsSurveyModel

__all__ = ["NpsResponseModel", "NpsSurveyModel"]
