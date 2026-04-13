from enum import StrEnum


class AssetType(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class StorageProvider(StrEnum):
    LOCAL = "LOCAL"
    S3 = "S3"
    R2 = "R2"


class AssetStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
