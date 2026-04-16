"""Referral code model — re-exported from shared for backward compatibility."""

# This model now lives in src.shared.infrastructure.models.crm so that
# analytics can import it without violating DDD boundaries.
from src.shared.infrastructure.models.crm import ReferralCodeModel

__all__ = ["ReferralCodeModel"]
