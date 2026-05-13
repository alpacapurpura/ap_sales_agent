"""Domain exceptions for analytics provider interactions.

Canonical location: src.shared.domain.ports
Re-exported here for backward compatibility — existing analytics code
imports from this module.
"""

from luana_core_platform.domain.ports import ConnectionRevokedError, TokenRefreshError

__all__ = ["ConnectionRevokedError", "TokenRefreshError"]
