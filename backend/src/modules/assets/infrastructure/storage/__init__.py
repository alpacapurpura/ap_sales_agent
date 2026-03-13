from .base import StorageStrategy
from .local import LocalStorageStrategy
from .r2 import R2StorageStrategy


def get_storage_strategy() -> StorageStrategy:
    """Return the configured storage strategy based on STORAGE_PROVIDER setting."""
    from src.core.config import settings

    if settings.STORAGE_PROVIDER.upper() == "R2":
        return R2StorageStrategy()
    return LocalStorageStrategy()


__all__ = ["StorageStrategy", "LocalStorageStrategy", "R2StorageStrategy", "get_storage_strategy"]
