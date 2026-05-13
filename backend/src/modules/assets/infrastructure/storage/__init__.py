"""Assets storage strategies package."""

from .base import StorageStrategy
from .local import LocalStorageStrategy
from .r2 import R2StorageStrategy


def get_storage_strategy() -> StorageStrategy:
    """Return the configured storage strategy based on STORAGE_PROVIDER setting."""
    from luana_core_platform.core.config import settings

    if settings.STORAGE_PROVIDER.upper() == "R2":
        return R2StorageStrategy()
    return LocalStorageStrategy()


__all__ = [
    "LocalStorageStrategy",
    "R2StorageStrategy",
    "StorageStrategy",
    "get_storage_strategy",
]
