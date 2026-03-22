"""Domain exceptions for analytics provider interactions."""

from typing import Optional


class ConnectionRevokedException(Exception):
    """Raised when a provider connection has been revoked or expired."""

    def __init__(self, message: str, channel_type: Optional[str] = None):
        super().__init__(message)
        self.channel_type = channel_type


class TokenRefreshFailed(Exception):
    """Raised when an OAuth token refresh attempt fails."""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
