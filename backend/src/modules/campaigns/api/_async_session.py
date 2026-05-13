"""Alias module — re-exports from _dependencies.py.

_service_factories.py imports from this module for backward-compat.
"""

from luana_core_campaigns.api._dependencies import (
    _AsyncSessionLocal,
    get_campaigns_async_session,
)

__all__ = ["_AsyncSessionLocal", "get_campaigns_async_session"]
