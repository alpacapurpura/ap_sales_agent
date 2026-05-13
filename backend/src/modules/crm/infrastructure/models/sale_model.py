"""CRM sale SQLAlchemy model — re-exported from shared for backward compatibility."""

# This model now lives in src.shared.infrastructure.models.crm so that
# analytics and other modules can import it without violating DDD boundaries.
# CRM-internal code still uses this path.
from luana_core_platform.infrastructure.models.crm import SaleModel

__all__ = ["SaleModel"]
