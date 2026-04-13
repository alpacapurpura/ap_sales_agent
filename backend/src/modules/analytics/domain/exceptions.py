"""Domain exceptions for analytics provider interactions."""


class ConnectionRevokedError(Exception):
    """Raised when a provider connection has been revoked or expired."""

    def __init__(self, message: str, channel_type: str | None = None):
        super().__init__(message)
        self.channel_type = channel_type


class TokenRefreshError(Exception):
    """Raised when an OAuth token refresh attempt fails."""

    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message)
        self.provider = provider
