"""Enumeration types for the assets domain."""

from enum import StrEnum


class AssetType(StrEnum):
    """Enumerate asset type values."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class StorageProvider(StrEnum):
    """Enumerate storage provider values."""

    LOCAL = "LOCAL"
    S3 = "S3"
    R2 = "R2"


class AssetStatus(StrEnum):
    """Enumerate asset status values."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
